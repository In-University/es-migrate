import jenkins.model.*
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

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

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
    Class workflowJobClass = Class.forName("org.jenkinsci.plugins.workflow.job.WorkflowJob")
    Class cpsFlowDefClass = Class.forName("org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition")

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
} catch (Exception e) {
    println "--> Skipping Pipeline job creation (plugin loading or missing): " + e.getMessage()
}

instance.save()
