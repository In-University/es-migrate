# Jenkins Terraform Module & Job Management Guide

This Terraform module deploys a Jenkins server on GCP Compute Engine using the official Docker image `jenkins/jenkins:2.504.3`. It automatically pre-installs essential plugins (Pipeline, Git, Job DSL, Matrix Authorization) and provisions parameterized sample jobs via Groovy startup scripts.

---

## 🚀 1. Deployment via Terraform

To deploy or update only the Jenkins module without affecting other infrastructure components:

```bash
cd terraform
terraform apply -target=module.jenkins -auto-approve
```

- **Reserved Internal IP**: `10.146.0.12`
- **Web Interface**: `http://<JENKINS_EXTERNAL_IP>:8080`
- **Default Credentials**: `admin` / `<var.elastic_password>`

---

## 🔄 2. Updating Job Configuration via REST API (Without VM Re-creation)

When modifying existing job configurations (e.g., build parameters, pipeline scripts) **without destroying or re-creating the VM instance**, update the job directly using the Jenkins REST API and `curl`.

### Step 1: Generate an API Token for the User (Web UI)
1. Log in to the Jenkins Web UI.
2. Click on the **User profile** in the top right corner -> select **Configure**.
3. Scroll down to the **API Token** section -> Click **Add new Token** -> Enter a name -> Click **Generate**.
4. Copy the generated token string (e.g., `11fca60401ca599d909ec75ce7a3b5a51d`).

### Step 2: Download the Job Configuration XML
The job URL on the Web UI maps directly to the REST API endpoint by appending `/config.xml` to the URL path.

```bash
curl -s -i -u "USERNAME:API_TOKEN" \
  http://localhost:8080/job/<JOB_NAME>/config.xml \
  -o config.xml
```

*Example:*
```bash
curl -s -i -u "testuser:11fca60401ca599d909ec75ce7a3b5a51d" \
  http://localhost:8080/job/sample-pipeline-job/config.xml \
  -o /tmp/job_config.xml
```

### Step 3: Modify Job Parameters in the XML File
Edit the desired parameters or script definitions in the downloaded XML file:

```bash
# Example: Change the default value of TARGET_INDEX from 'bench-es9' to 'bench-es9-production'
sed -i 's/bench-es9/bench-es9-production/g' /tmp/job_config.xml
```

### Step 4: Upload (POST) the Modified XML back to Jenkins
```bash
curl -s -i -u "USERNAME:API_TOKEN" \
  -H "Content-Type: application/xml" \
  -X POST http://localhost:8080/job/<JOB_NAME>/config.xml \
  --data-binary @/tmp/job_config.xml
```

*Example:*
```bash
curl -s -i -u "testuser:11fca60401ca599d909ec75ce7a3b5a51d" \
  -H "Content-Type: application/xml" \
  -X POST http://localhost:8080/job/sample-pipeline-job/config.xml \
  --data-binary @/tmp/job_config.xml
```

A response header returning **`HTTP/1.1 200 OK`** confirms that the job configuration was successfully updated on the server.

---

## 🛠️ 3. Explanation of `curl` Flags Used

- **`-s` (`--silent`)**: Enables silent mode by hiding progress meters and non-critical messages for a clean output.
- **`-i` (`--include`)**: Includes HTTP response headers (e.g., `HTTP/1.1 200 OK`) in the output to easily verify HTTP status codes.
- **`-u` (`--user`)**: Passes credentials in `username:api_token` format using standard HTTP Basic Authentication headers.
- **`-H "Content-Type: application/xml"`**: Specifies that the payload being uploaded is in XML format.
- **`-X POST`**: Specifies the HTTP POST method to overwrite the configuration.
- **`--data-binary @<file_path>`**: Transmits the XML payload as binary data to preserve line breaks and formatting.

---

## 🔐 4. User Access Management (Matrix Security)

To configure permissions allowing a non-admin user to manage jobs (Build / Create / Delete / Update) while restricting access to administrative settings (`Manage Jenkins`):

1. Navigate to **Manage Jenkins** -> **Security**.
2. Under the **Authorization** section, select **Matrix-based security**.
3. Add the target user (e.g., `testuser`) and assign the following permissions:
   - **Overall**: Check `Read` (do **NOT** check `Administer`).
   - **Job**: Check `Create`, `Configure`, `Delete`, `Build`, `Read`, `Cancel`, and `Workspace`.
4. Click **Save**.

---

## ⚡ 5. Automated Parameter Updates via Containerized Jenkins CLI Pipeline

Instead of using `curl` externally, Jenkins can run a self-updating Pipeline job (`update-job-parameters`) directly inside the Jenkins Docker container.

### How it works:
1. **Java Runtime**: Jenkins runs inside Docker with Java preinstalled.
2. **CLI Download**: The job downloads `jenkins-cli.jar` directly from `http://localhost:8080/jnlpJars/jenkins-cli.jar`.
3. **Authentication**: Uses Jenkins Credentials (`Username with password`) stored under Credentials ID `my-jenkins-token` (Username: `<admin_user>`, Password: `<api_token>`).
4. **Execution Flow**:
   - `get-job`: Fetches current job configuration XML (`sample-pipeline-job`).
   - `sed`: Updates default parameter value (`TARGET_INDEX`) directly in `config.xml`.
   - `update-job`: Applies the updated XML configuration back to Jenkins via `jenkins-cli.jar`.

### Steps to Run:
1. Go to **Manage Jenkins** -> **Credentials** -> **System** -> **Global credentials**.
2. Add Credentials:
   - **Kind**: Username with password
   - **Username**: `admin` (or your Jenkins user)
   - **Password**: `<YOUR_API_TOKEN>`
   - **ID**: `my-jenkins-token`
3. Trigger **`update-job-parameters`** with desired parameters (`TARGET_JOB`, `NEW_TARGET_INDEX`, `NEW_ACTION`, `NEW_DRY_RUN`).

