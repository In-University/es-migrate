import jenkins.model.*
import jenkins.install.*
import hudson.model.*
import hudson.security.*
import hudson.tasks.Shell

def instance = Jenkins.getInstance()

// 1. Bypass setup wizard
instance.setInstallState(InstallState.INITIAL_SETUP_COMPLETED)

// 2. Create Admin user & enable basic security
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("${jenkins_admin_user}", "${jenkins_admin_password}")
instance.setSecurityRealm(hudsonRealm)

try {
    def strategy = new hudson.security.ProjectMatrixAuthorizationStrategy()
    strategy.add(Jenkins.ADMINISTER, "${jenkins_admin_user}")
    instance.setAuthorizationStrategy(strategy)
    println "--> Configured ProjectMatrixAuthorizationStrategy for user '${jenkins_admin_user}'."
} catch (Throwable t) {
    println "--> Matrix Auth plugin unavailable, falling back to FullControlOnceLoggedIn: " + t.getMessage()
    def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
    strategy.setAllowAnonymousRead(false)
    instance.setAuthorizationStrategy(strategy)
}

// 2.5 Auto-generate API token & 'my-jenkins-token' credential for CLI automation
try {
    def u = User.get("${jenkins_admin_user}", false)
    if (u != null) {
        def apiTokenProp = u.getProperty(jenkins.security.apitoken.ApiTokenProperty.class)
        def tokenResult = apiTokenProp.tokenStore.generateToken("auto-cli-token")
        u.save()
        
        def domain = com.cloudbees.plugins.credentials.domains.Domain.global()
        def store = instance.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()
        def cred = new com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl(
            com.cloudbees.plugins.credentials.CredentialsScope.GLOBAL,
            "my-jenkins-token",
            "Auto-generated API Token for CLI updates",
            "${jenkins_admin_user}",
            tokenResult.plainValue
        )
        store.addCredentials(domain, cred)
        println "--> Auto-created 'my-jenkins-token' credential for user '${jenkins_admin_user}'."
    }
} catch (Throwable t) {
    println "--> Could not auto-create my-jenkins-token credential: " + t.getMessage()
}

instance.save()

// 3. Create Sample Parameterized Freestyle Job
def jobName = "sample-job"
if (instance.getItem(jobName) == null) {
    def project = new FreeStyleProject(instance, jobName)
    project.setDescription("Sample Parameterized Freestyle Job auto-created by Terraform startup script")
    
    // Define Build Parameters (String, Choice, Boolean)
    def paramDefs = [
        new StringParameterDefinition("TARGET_INDEX", "bench-es9", "Target Elasticsearch Index name"),
        new ChoiceParameterDefinition("ACTION", ["migrate", "rollback", "verify"] as String[], "Execution Action"),
        new BooleanParameterDefinition("DRY_RUN", false, "Enable dry-run mode without modifying data")
    ]
    project.addProperty(new ParametersDefinitionProperty(paramDefs))
    
    // Add shell build step accessing the parameters
    def shellScript = '''echo "========================================="
echo "Jenkins Parameterized Job Execution"
echo "Target Index : $${TARGET_INDEX}"
echo "Action       : $${ACTION}"
echo "Dry Run      : $${DRY_RUN}"
echo "Execution Date: $(date)"
echo "========================================="'''
    
    project.getBuildersList().add(new Shell(shellScript))
    project.save()
    println "--> Created parameterized freestyle job '$${jobName}' successfully."
}

// 4. Create Sample Parameterized Pipeline Job (using reflection to avoid classloader errors if plugin is loading)
def pipelineJobName = "sample-pipeline-job"
try {
    ClassLoader classLoader = instance.getPluginManager().uberClassLoader
    Class workflowJobClass = classLoader.loadClass("org.jenkinsci.plugins.workflow.job.WorkflowJob")
    Class cpsFlowDefClass = classLoader.loadClass("org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition")

    if (instance.getItem(pipelineJobName) == null) {
        def pipeJob = instance.createProject(workflowJobClass, pipelineJobName)
        pipeJob.setDescription("Sample Parameterized Pipeline Job auto-created by Terraform startup script")
        
        def pipeScript = '''pipeline {
    agent any
    parameters {
        string(name: 'TARGET_INDEX', defaultValue: 'bench-es9', description: 'Target Index')
        choice(name: 'ACTION', choices: ['migrate', 'rollback', 'verify'], description: 'Action')
        booleanParam(name: 'DRY_RUN', defaultValue: false, description: 'Dry run')
    }
    stages {
        stage('Initialize') {
            steps {
                echo "Starting Pipeline execution..."
                echo "Target Index : $${params.TARGET_INDEX}"
                echo "Action       : $${params.ACTION}"
                echo "Dry Run      : $${params.DRY_RUN}"
            }
        }
        stage('Execute') {
            steps {
                sh 'echo "Running migration script..." && date'
            }
        }
    }
}'''
        def flowDef = cpsFlowDefClass.getConstructor(String.class, boolean.class).newInstance(pipeScript, true)
        pipeJob.setDefinition(flowDef)
        pipeJob.save()
        println "--> Created sample pipeline job '$${pipelineJobName}' successfully."
    }

    // 5. Create CLI Job Parameter Updater Pipeline Job
    def updateJobName = "update-job-parameters"
    if (instance.getItem(updateJobName) == null) {
        def updateJob = instance.createProject(workflowJobClass, updateJobName)
        updateJob.setDescription("Pipeline job to programmatically update parameter default values of target jobs via jenkins-cli.jar")
        
        def updateScript = '''pipeline {
    agent any

    parameters {
        string(name: 'TARGET_JOB', defaultValue: 'sample-pipeline-job', description: 'Name of the Jenkins job to update')
        string(name: 'NEW_TARGET_INDEX', defaultValue: 'bench-es9-updated', description: 'New default value for TARGET_INDEX')
        choice(name: 'NEW_ACTION', choices: ['migrate', 'rollback', 'verify'], description: 'New default selection for ACTION')
        booleanParam(name: 'NEW_DRY_RUN', defaultValue: true, description: 'New default boolean value for DRY_RUN')
        string(name: 'CREDENTIALS_ID', defaultValue: 'my-jenkins-token', description: 'Jenkins Credentials ID (User/API Token)')
    }

    environment {
        JENKINS_URL = 'http://localhost:8080'
        TARGET_JOB = "$${params.TARGET_JOB}"
        NEW_TARGET_INDEX = "$${params.NEW_TARGET_INDEX}"
        CREDENTIALS_ID = "$${params.CREDENTIALS_ID}"
    }

    stages {
        stage('Download Jenkins CLI') {
            steps {
                sh \'\'\'
                    set -eu
                    echo "[CLI] Downloading jenkins-cli.jar from $${JENKINS_URL}..."
                    curl -sSL $${JENKINS_URL}/jnlpJars/jenkins-cli.jar -o jenkins-cli.jar
                \'\'\'
            }
        }

        stage('Fetch Job Config') {
            steps {
                withCredentials([usernamePassword(credentialsId: "$${env.CREDENTIALS_ID}", passwordVariable: 'API_TOKEN', usernameVariable: 'USER')]) {
                    sh \'\'\'
                        set -eu
                        echo "[CLI] Fetching configuration for job: $${TARGET_JOB}..."
                        java -jar jenkins-cli.jar -s $${JENKINS_URL} -auth "$USER:$API_TOKEN" get-job "$${TARGET_JOB}" > config.xml
                        grep -A 4 "<name>TARGET_INDEX</name>" config.xml || true
                    \'\'\'
                }
            }
        }

        stage('Update Config XML') {
            steps {
                sh \'\'\'
                    set -eu
                    echo "[CLI] Checking if TARGET_INDEX parameter exists in config.xml..."
                    if ! grep -q "<name>TARGET_INDEX</name>" config.xml; then
                        echo "[WARNING] Parameter TARGET_INDEX not found in $${TARGET_JOB}."
                    else
                        echo "[CLI] Updating TARGET_INDEX default value to $${NEW_TARGET_INDEX} in config.xml..."
                        SAFE_INDEX=$(echo "$${NEW_TARGET_INDEX}" | tr -d '#&')
                        sed -i '/<name>TARGET_INDEX/,/defaultValue/ s#<defaultValue>.*</defaultValue>#<defaultValue>'"$${SAFE_INDEX}"'</defaultValue>#' config.xml
                    fi

                    echo "[CLI] Updated config XML preview:"
                    grep -A 4 "<name>TARGET_INDEX</name>" config.xml || true
                \'\'\'
            }
        }

        stage('Apply Job Update') {
            steps {
                withCredentials([usernamePassword(credentialsId: "$${env.CREDENTIALS_ID}", passwordVariable: 'API_TOKEN', usernameVariable: 'USER')]) {
                    sh \'\'\'
                        set -eu
                        echo "[CLI] Applying updated configuration to job: $${TARGET_JOB}..."
                        java -jar jenkins-cli.jar -s $${JENKINS_URL} -auth "$USER:$API_TOKEN" update-job "$${TARGET_JOB}" < config.xml
                        echo "[CLI] Job configuration updated successfully!"
                    \'\'\'
                }
            }
        }

        stage('Verify Update') {
            steps {
                withCredentials([usernamePassword(credentialsId: "$${env.CREDENTIALS_ID}", passwordVariable: 'API_TOKEN', usernameVariable: 'USER')]) {
                    sh \'\'\'
                        set -eu
                        echo "[CLI] Verifying updated job parameters..."
                        java -jar jenkins-cli.jar -s $${JENKINS_URL} -auth "$USER:$API_TOKEN" get-job "$${TARGET_JOB}" > verified_config.xml
                        grep -A 4 "<name>TARGET_INDEX</name>" verified_config.xml || true
                    \'\'\'
                }
            }
        }
    }
}'''
        def flowDef2 = cpsFlowDefClass.getConstructor(String.class, boolean.class).newInstance(updateScript, true)
        updateJob.setDefinition(flowDef2)
        updateJob.save()
        println "--> Created update pipeline job '$${updateJobName}' successfully."
    }
} catch (Exception e) {
    println "--> Skipping Pipeline job creation (plugin loading or missing): " + e.getMessage()
}

instance.save()
