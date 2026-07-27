// ES6 <- ES9 blue-green rollback.
//
// One stage per index, running scripts/es_rollback_py.sh with that index's
// timestamp field. The script itself handles exactly one index; the ordering
// and the per-index isolation live here, which is also what buys the
// per-stage log, retry and timing that Jenkins gives for free.
//
// This pipeline is self-contained: it drives scripts/es_rollback_py.sh and
// nothing else. scripts/es_rollback_all.sh does the same job for a by-hand
// run on the VM and is deliberately NOT called from here -- neither path
// should break because the other moved. The price is the index map below,
// which has to be kept in step with the one in es_rollback_all.sh.
//
// Sequential on purpose: the delta sync already fans out across shards, and
// ES6 is disk-bound during a rollback, so two indices at once make both
// slower. A failing index does not stop the others -- one bad index should
// not cost the window for the rest.
//
// Exit codes from the script: 0 ok, 2 dead letters (UNSTABLE), 1 fatal
// (FAILURE), 130 interrupted (ABORTED).

// Index -> the field a write on that index bumps. The name is the same on
// both clusters because both address the alias (products -> products_v1.0.1).
INDEX_TS = [
  'products': 'updated_at',
  'orders'  : 'system_update_at',
]

pipeline {
  agent { label 'es-migrate' }

  parameters {
    choice(
      name: 'COMMAND',
      choices: ['preflight', 'run', 'resume', 'verify', 'status', 'undo'],
      description: 'preflight writes nothing. Start there.')
    string(
      name: 'ONLY',
      defaultValue: '',
      description: 'Space- or comma-separated indices. Empty runs all of them.')
    booleanParam(
      name: 'ASSUME_YES',
      defaultValue: false,
      description: 'Skip the delete blast-radius confirmation. Only after reading to_delete.')
    booleanParam(
      name: 'ALLOW_PARTIAL',
      defaultValue: false,
      description: 'Let the delta gate pass with dead letters. Those docs stay missing from ES6.')
  }

  options {
    timestamps()
    disableConcurrentBuilds()          // the script takes a per-state-dir lock anyway
    buildDiscarder(logRotator(numToKeepStr: '30'))
    timeout(time: 12, unit: 'HOURS')
  }

  environment {
    ES6_URL    = "${env.ES6_URL ?: 'http://es6-dest:9200'}"
    ES9_URL    = "${env.ES9_URL ?: 'http://es9-dest:9200'}"
    ELASTIC_PW = credentials('elastic-password')
    // Outside the workspace: state and journal must survive a workspace
    // wipe, because `resume` and `undo` are worthless without them.
    STATE_ROOT = '/var/lib/es-rollback'
  }

  stages {
    stage('tools') {
      steps {
        sh '''
          set -eu
          for b in curl jq python3 awk sort comm gzip split; do
            command -v "$b" >/dev/null || { echo "missing: $b" >&2; exit 1; }
          done
          mkdir -p "$STATE_ROOT"
        '''
      }
    }

    stage('resolve indices') {
      steps {
        script {
          // An unknown name is a typo, and a typo that silently selected
          // nothing would read as "that index had no work to do".
          def wanted = params.ONLY.trim()
            ? params.ONLY.split(/[,\s]+/).collect { it.trim() }.findAll { it }
            : INDEX_TS.keySet().sort()

          def unknown = wanted.findAll { !INDEX_TS.containsKey(it) }
          if (unknown) {
            error("ONLY names indices that are not in the map: ${unknown.join(', ')}" +
                  " (have: ${INDEX_TS.keySet().sort().join(', ')})")
          }

          SELECTED = wanted
          echo "will run '${params.COMMAND}' on: ${SELECTED.join(', ')}"
          currentBuild.description = "${params.COMMAND}: ${SELECTED.join(', ')}"
        }
      }
    }

    // undo rewrites every document the run touched and deletes the ones it
    // created. It is correct and it is tested, but it is also the one command
    // whose blast radius is the whole index, so it does not start on a
    // mis-click. agent none so the prompt does not pin an executor while it
    // waits.
    stage('confirm undo') {
      when { expression { params.COMMAND == 'undo' } }
      agent none
      steps {
        script {
          timeout(time: 30, unit: 'MINUTES') {
            input(
              message: """Restore ES6 from the journal for: ${SELECTED.join(', ')}?

This overwrites every document the run wrote and deletes every document it
created, using the pre-images in ${env.STATE_ROOT}/<index>/journal.tsv.gz.
Only the CURRENT run is replayed -- archived journals are not.""",
              ok: 'Run undo')
          }
        }
      }
    }

    stage('rollback') {
      steps {
        script {
          for (idx in SELECTED) {
            // Capture per iteration; a bare reference would read the last
            // value by the time the closure runs.
            def index = idx
            def tsField = INDEX_TS[index]

            stage("${index}") {
              // A failed index marks its own stage and the build, then lets
              // the loop carry on to the next one.
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                withEnv([
                  "SRC_INDEX=${index}",
                  "DST_INDEX=${index}",
                  "TS_FIELD=${tsField}",
                  "STATE_DIR=${env.STATE_ROOT}/${index}",
                  "ASSUME_YES=${params.ASSUME_YES}",
                  "ALLOW_PARTIAL=${params.ALLOW_PARTIAL}",
                ]) {
                  def rc = sh(
                    returnStatus: true,
                    script: "bash scripts/es_rollback_py.sh ${params.COMMAND}")

                  // 2 is "finished, but some documents were rejected by ES6"
                  // -- real work landed, and the dead letter file is the
                  // thing to look at. That is UNSTABLE, not FAILURE.
                  if (rc == 2) {
                    unstable("${index}: finished with dead letters -- see ${env.STATE_ROOT}/${index}/deadletter.ndjson")
                  } else if (rc == 130) {
                    error("${index}: interrupted")
                  } else if (rc != 0) {
                    error("${index}: es_rollback_py.sh exited ${rc}")
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  post {
    always {
      script {
        def indices = binding.hasVariable('SELECTED') ? SELECTED : INDEX_TS.keySet().sort()
        def row = { c -> String.format('%-24s %-16s %18s %9s %9s %11s',
                                       c[0], c[1], c[2], c[3], c[4], c[5]) }
        def lines = [row(['INDEX', 'PHASE', 'SEEN/SYNCED', 'DELETED', 'REPAIRED', 'DEADLETTER'])]
        def phases = []

        for (idx in indices) {
          def path = "${env.STATE_ROOT}/${idx}/state.env"
          def kv = [:]
          if (fileExists(path)) {
            readFile(path).split('\n').each { line ->
              def i = line.indexOf('=')
              if (i > 0) { kv[line.substring(0, i).trim()] = line.substring(i + 1).trim() }
            }
          }
          def get = { k, d -> kv.containsKey(k) && kv[k] ? kv[k] : d }
          lines << row([idx, get('PHASE', 'none'),
                        "${get('SEEN', '0')}/${get('SYNCED', '0')}",
                        get('DELETED', '-'), get('REPAIRED', '-'), get('DL_COUNT', '0')])
          phases << "${idx}=${get('PHASE', 'none')}"
        }

        echo "\n========== summary (${params.COMMAND}) ==========\n" +
             lines.join('\n') +
             "\n\nstate: ${env.STATE_ROOT}/<index>/   " +
             "dead letters: ${env.STATE_ROOT}/<index>/deadletter.ndjson"

        // Phases on the build page, so a glance at the history says which
        // indices finished without opening the log.
        currentBuild.description = "${params.COMMAND} — ${phases.join(' ')}"
      }

      // The run log and the id diffs are what any post-mortem starts from,
      // and they live outside the workspace, so copy them in to archive.
      sh '''
        set -eu
        rm -rf artifacts && mkdir -p artifacts
        for d in "$STATE_ROOT"/*/; do
          [ -d "$d" ] || continue
          n="$(basename "$d")"
          mkdir -p "artifacts/$n"
          for f in run.log state.env deadletter.ndjson to_delete to_repair \
                   verify_extra verify_missing verify_sample_diff; do
            [ -f "$d$f" ] && cp "$d$f" "artifacts/$n/" || true
          done
        done
      '''
      archiveArtifacts artifacts: 'artifacts/**', allowEmptyArchive: true, fingerprint: false
    }
  }
}
