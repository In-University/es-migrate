// ES6 <- ES9 blue-green rollback.
//
// One stage per index, running scripts/es_rollback_py.sh.
// The script handles one index at a time; ordering and per-index isolation
// live here, providing per-stage logs, retries, and timing in Jenkins.
//
// State is pulled from GCS Bucket before running each index, uploaded back
// to GCS Bucket immediately after, and then deleted locally (rm -rf) to save disk.

// Array of index names to run rollback for.
INDICES = ['products', 'orders']

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
    string(
      name: 'SRC_INDEX',
      defaultValue: '',
      description: 'Source Index name on ES9 (leave empty to use index name from list)')
    string(
      name: 'DST_INDEX',
      defaultValue: '',
      description: 'Destination Index name on ES6 (leave empty to use index name from list)')
    string(
      name: 'ES6_URL',
      defaultValue: 'http://es6-dest:9200',
      description: 'Destination ES6 Cluster URL')
    string(
      name: 'ES6_USER',
      defaultValue: 'elastic',
      description: 'ES6 Username')
    password(
      name: 'ES6_PW',
      defaultValue: 'elastic',
      description: 'ES6 Password')
    string(
      name: 'ES9_URL',
      defaultValue: 'http://es9-dest:9200',
      description: 'Source ES9 Cluster URL')
    string(
      name: 'ES9_USER',
      defaultValue: 'elastic',
      description: 'ES9 Username')
    password(
      name: 'ES9_PW',
      defaultValue: 'elastic',
      description: 'ES9 Password')
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
    TS_FIELD      = "${env.TS_FIELD ?: 'modified_at'}"
    REMOVE_FIELDS = "${env.REMOVE_FIELDS ?: 'modified_at'}"
    GCS_BUCKET    = "${env.GCS_BUCKET ?: 'es-migrate-rollback-state'}"
    STATE_ROOT    = "${env.STATE_ROOT ?: "${env.WORKSPACE}/.rollback-state"}"
  }

  stages {
    stage('tools') {
      steps {
        sh '''
          set -eu
          for b in curl jq python3 awk sort comm gzip split gsutil; do
            command -v "$b" >/dev/null || { echo "missing: $b" >&2; exit 1; }
          done
          mkdir -p "$STATE_ROOT"
          avail_kb=$(df -k "$STATE_ROOT" | awk 'NR==2 {print $4}')
          avail_mb=$((avail_kb / 1024))
          avail_gb=$(awk -v m="$avail_mb" 'BEGIN {printf "%.2f", m/1024}')
          echo "Available disk space on $STATE_ROOT: ${avail_mb} MB (${avail_gb} GB)"
          if [ "$avail_kb" -lt 1048576 ]; then
            echo "ERROR: Insufficient disk space on $STATE_ROOT! Required >= 1GB (1024MB), available: ${avail_mb}MB" >&2
            exit 1
          fi
        '''
      }
    }

    stage('resolve indices') {
      steps {
        script {
          def wanted = params.ONLY.trim()
            ? params.ONLY.split(/[,\s]+/).collect { it.trim() }.findAll { it }
            : INDICES.sort()

          def unknown = wanted.findAll { !INDICES.contains(it) }
          if (unknown) {
            error("ONLY names indices that are not in the list: ${unknown.join(', ')}" +
                  " (have: ${INDICES.sort().join(', ')})")
          }

          SELECTED = wanted
          echo "will run '${params.COMMAND}' on: ${SELECTED.join(', ')} (TS_FIELD=${env.TS_FIELD}, REMOVE_FIELDS=${env.REMOVE_FIELDS})"
          currentBuild.description = "${params.COMMAND}: ${SELECTED.join(', ')}"
        }
      }
    }

    stage('confirm undo') {
      when { expression { params.COMMAND == 'undo' } }
      agent none
      steps {
        script {
          timeout(time: 30, unit: 'MINUTES') {
            input(
              message: """Restore ES6 from the journal for: ${SELECTED.join(', ')}?

This overwrites every document the run wrote and deletes every document it
created, using the pre-images in gs://${env.GCS_BUCKET}/rollback-state/<index>/journal.tsv.gz.
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
            def index = idx
            def srcIdx = params.SRC_INDEX.trim() ? params.SRC_INDEX.trim() : index
            def dstIdx = params.DST_INDEX.trim() ? params.DST_INDEX.trim() : index

            stage("${index}") {
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                withEnv([
                  "ES6_URL=${params.ES6_URL}",
                  "ES6_USER=${params.ES6_USER}",
                  "ES6_PW=${params.ES6_PW}",
                  "ES9_URL=${params.ES9_URL}",
                  "ES9_USER=${params.ES9_USER}",
                  "ES9_PW=${params.ES9_PW}",
                  "ELASTIC_PW=${params.ES6_PW}",
                  "SRC_INDEX=${srcIdx}",
                  "DST_INDEX=${dstIdx}",
                  "TS_FIELD=${env.TS_FIELD}",
                  "REMOVE_FIELDS=${env.REMOVE_FIELDS}",
                  "STATE_DIR=${env.STATE_ROOT}/${index}",
                  "ASSUME_YES=${params.ASSUME_YES}",
                  "ALLOW_PARTIAL=${params.ALLOW_PARTIAL}",
                ]) {
                  // 1. Pull state from GCS Bucket before running
                  sh '''
                    set -eu
                    mkdir -p "$STATE_DIR"
                    echo ">> Pulling state from gs://${GCS_BUCKET}/rollback-state/${SRC_INDEX}..."
                    gsutil -m rsync -r "gs://${GCS_BUCKET}/rollback-state/${SRC_INDEX}" "$STATE_DIR" || true
                  '''

                  // 2. Execute rollback command
                  def rc = sh(
                    returnStatus: true,
                    script: "bash scripts/es_rollback_py.sh ${params.COMMAND}")

                  // 3. Sync state back to GCS Bucket, backup lightweight summary files, and clean up heavy local dir
                  sh '''
                    set -eu
                    echo ">> Syncing updated state to gs://${GCS_BUCKET}/rollback-state/${SRC_INDEX}..."
                    gsutil -m rsync -r "$STATE_DIR" "gs://${GCS_BUCKET}/rollback-state/${SRC_INDEX}" || true

                    echo ">> Backing up lightweight metadata for Jenkins summary..."
                    mkdir -p "$STATE_ROOT/summary/$SRC_INDEX"
                    cp "$STATE_DIR/state.env" "$STATE_ROOT/summary/$SRC_INDEX/" 2>/dev/null || true
                    cp "$STATE_DIR/deadletter.ndjson" "$STATE_ROOT/summary/$SRC_INDEX/" 2>/dev/null || true
                    cp "$STATE_DIR/run.log" "$STATE_ROOT/summary/$SRC_INDEX/" 2>/dev/null || true

                    echo ">> Cleaning up local STATE_DIR to free disk space..."
                    rm -rf "$STATE_DIR"
                  '''

                  if (rc == 2) {
                    unstable("${index}: finished with dead letters -- see gs://${env.GCS_BUCKET}/rollback-state/${index}/deadletter.ndjson")
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
        def indices = binding.hasVariable('SELECTED') ? SELECTED : INDICES.sort()
        def row = { c -> String.format('%-24s %-16s %18s %9s %9s %11s',
                                       c[0], c[1], c[2], c[3], c[4], c[5]) }
        def lines = [row(['INDEX', 'PHASE', 'SEEN/SYNCED', 'DELETED', 'REPAIRED', 'DEADLETTER'])]
        def phases = []

        for (idx in indices) {
          def path = "${env.STATE_ROOT}/summary/${idx}/state.env"
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
             "\n\nstate: gs://${env.GCS_BUCKET}/rollback-state/<index>/   " +
             "dead letters: gs://${env.GCS_BUCKET}/rollback-state/<index>/deadletter.ndjson"

        currentBuild.description = "${params.COMMAND} — ${phases.join(' ')}"
      }

      sh '''
        set -eu
        rm -rf artifacts && mkdir -p artifacts
        if [ -d "$STATE_ROOT/summary" ]; then
          for d in "$STATE_ROOT/summary"/*/; do
            [ -d "$d" ] || continue
            n="$(basename "$d")"
            mkdir -p "artifacts/$n"
            cp "$d"* "artifacts/$n/" 2>/dev/null || true
          done
          rm -rf "$STATE_ROOT/summary"
        fi
      '''
      archiveArtifacts artifacts: 'artifacts/**', allowEmptyArchive: true, fingerprint: false
    }
  }
}
