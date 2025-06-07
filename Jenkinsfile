// Jenkinsfile (Declarative Pipeline)

pipeline {
    agent any // Or a specific agent if you have labels, e.g., agent { label 'my-jenkins-agent' }

    environment {
        // Define environment variables used throughout the pipeline
        // Make sure these match your actual Jenkins Global properties or credential binding names
        // RENDER_DEPLOY_HOOK_URL is handled via withCredentials for security
        // RENDER_AUTH_TOKEN is mentioned in logs but not used in the provided curl,
        //   so it's kept masked but not explicitly used in this example.
        // STAGING_URL could be a direct URL or derived
        STAGING_URL = 'https://majd-kassem-business-dev.onrender.com'
        // Define repository for SUT if different from the Jenkinsfile repo
        SUT_REPO = 'https://github.com/majd-j-kassem/majd.kassem.business.git'
        SUT_BRANCH = 'dev'
    }

    tools {
        // Define the tools required for your pipeline.
        // These refer to tools configured in Jenkins -> Manage Jenkins -> Tools
        nodejs 'NodeJS_24' // As seen in your logs, 'NodeJS_24' is used for Node.js
        // If you have a specific Python installation configured as a Jenkins Tool,
        // you might define it here, e.g., python 'Python3.10'.
        // However, your log shows 'python3 -m venv', implying system Python.
        // Allure Commandline is also used for reporting.
        allure 'Allure_2.34.0' // As seen in your logs, 'Allure_2.34.0'
    }

    stages {
        stage('Declarative: Checkout SCM') {
            steps {
                // This step automatically checks out the Jenkinsfile repository
                // based on the SCM configuration of the Jenkins job itself.
                // The credential '8433ffe6-8d5e-40fb-9e5d-016a75096e05' is from your log.
                checkout([$class: 'GitSCM', branches: [[name: 'refs/remotes/origin/dev']],
                          doGenerateSubmoduleConfigurations: false, extensions: [], gitTool: 'Default',
                          userRemoteConfigs: [[credentialsId: '8433ffe6-8d5e-40fb-9e5d-016a75096e05', url: "${env.SUT_REPO}"]]])
            }
        }

        stage('Test NodeJS Tool') {
            steps {
                script {
                    echo "Attempting to use NodeJS tool..."
                    sh 'node -v'
                    sh 'npm -v'
                }
            }
        }

        stage('Checkout SUT Dev') {
            steps {
                script {
                    echo "Checking out SUT repository: ${env.SUT_REPO}, branch: ${env.SUT_BRANCH}"
                    dir('sut-code') { // Checkout the SUT code into a 'sut-code' subdirectory
                        git branch: "${env.SUT_BRANCH}",
                            credentialsId: 'git_id', // Assuming 'git_id' is your Git credential for the SUT repo
                            url: "${env.SUT_REPO}"
                    }
                }
            }
        }

        stage('Setup Python Environment (SUT)') {
            steps {
                script {
                    echo "Setting up Python virtual environment and installing dependencies for SUT..."
                    dir('sut-code/my_learning_platform') { // Assuming your Python project is in 'my_learning_platform'
                        sh '''
                            python3 -m venv .venv
                            source .venv/bin/activate
                            pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    }
                }
            }
        }

        stage('Setup NodeJS and Newman (SUT)') {
            steps {
                script {
                    echo "Installing Newman and Allure reporter..."
                    // Clean up old installations and install latest
                    sh '''
                        npm cache clean --force
                        rm -rf "${TOOL_HOME}/newman"
                        rm -rf "${TOOL_HOME}/newman-reporter-allure"
                        rm -rf "${TOOL_HOME}/newman-reporter-htmlextra"
                        npm install -g newman@latest newman-reporter-allure@latest newman-reporter-htmlextra@latest
                    '''
                    // Note: TOOL_HOME is a Jenkins environment variable that points to the tool installation directory
                    // You might need to adjust 'TOOL_HOME' or the path if your Node.js tool is installed differently.
                    // The paths `/var/lib/jenkins/tools/jenkins.plugins.nodejs.tools.NodeJSInstallation/NodeJS_24/lib/node_modules/`
                    // seen in your logs are specific to the Jenkins agent's tool installation.
                    // Using `npm install -g` usually handles putting them in the correct PATH for the Node.js tool.
                }
            }
        }

        stage('Run Unit Tests (SUT)') {
            steps {
                script {
                    echo "Running Django unit tests with pytest and generating Allure and JUnit results..."
                    dir('sut-code/my_learning_platform') {
                        sh 'rm -rf ../../allure-results/unit-tests' // Clear old results
                        sh 'mkdir -p ../../allure-results/unit-tests'
                        sh 'mkdir -p ../../junit-reports'
                        sh '''
                            source .venv/bin/activate
                            pytest --alluredir=../../allure-results/unit-tests \\
                                   --junitxml=../../junit-reports/sut_unit_report.xml \\
                                   accounts/tests/unit/
                        '''
                    }
                }
            }
        }

        stage('Run Integration Tests (SUT)') {
            steps {
                script {
                    echo "Running Django integration tests with pytest and generating Allure results..."
                    dir('sut-code/my_learning_platform') {
                        sh 'rm -rf ../../allure-results/integration-tests' // Clear old results
                        sh 'mkdir -p ../../allure-results/integration-tests'
                        sh 'mkdir -p ../../junit-reports' // Ensure this exists for JUnit XML if needed
                        sh '''
                            source .venv/bin/activate
                            pytest --alluredir=../../allure-results/integration-tests \\
                                   --junitxml=../../junit-reports/sut_integration_report.xml \\
                                   accounts/tests/integration/
                        '''
                    }
                }
            }
        }

        stage('Build and Deploy SUT to Staging (via Render)') {
            steps {
                script {
                    // Use withCredentials to inject the secret RENDER_DEPLOY_HOOK_URL safely
                    withCredentials([string(credentialsId: 'RENDER_DEPLOY_HOOK_URL', variable: 'RENDER_DEPLOY_HOOK_URL')]) {
                        echo "Triggering Render deployment for ${env.STAGING_URL}..."

                        def deployResponse = ''
                        def curlExitStatus = -1 // Initialize with a non-zero value to detect if curl wasn't even run

                        try {
                            // Execute curl command and capture both stdout and status
                            // IMPORTANT: `returnStdout: true` is crucial for getting the response content.
                            def curlResult = sh(script: """
                                curl -v -X POST "${RENDER_DEPLOY_HOOK_URL}"
                            """, returnStdout: true, returnStatus: true, encoding: 'UTF-8')

                            deployResponse = curlResult.stdout.trim() // Trim to remove potential leading/trailing whitespace
                            curlExitStatus = curlResult.status

                            echo "Curl Command Exit Status: ${curlExitStatus}"
                            echo "Full Curl Response Output (from stdout):"
                            echo "${deployResponse}" // This will now show the actual 44-byte response from Render

                            // Check if the curl command itself had a non-zero exit status
                            if (curlExitStatus != 0) {
                                error "Curl command failed with exit status ${curlExitStatus}. Render deploy hook might be incorrect or unreachable. Response: ${deployResponse}"
                            }

                            // --- CRITICAL ADAPTATION NEEDED HERE ---
                            // Based on your logs, Render returns `text/plain` with 44 bytes.
                            // You MUST inspect what those 44 bytes actually are and adjust the logic below.
                            // Here are some common scenarios and how to handle them:

                            // Scenario 1: The 44-byte response is a simple success message (e.g., "Deployment initiated successfully.")
                            if (deployResponse.contains("Deployment initiated successfully.") || deployResponse.equals("ok") || deployResponse.length() > 0) {
                                echo "Render deploy hook successfully acknowledged the deployment initiation."
                                // If you need the deploy ID, you cannot get it from this plain text response.
                                // You would need to check the Render dashboard manually or use Render's API (requiring RENDER_AUTH_TOKEN)
                                // to poll for the latest deployment status of your service (using its service ID).
                                // For now, we proceed assuming triggering is enough for this stage.
                            }
                            // Scenario 2: The 44-byte response is an error message from Render itself.
                            else if (deployResponse.contains("Error") || deployResponse.contains("Failed")) { // Example error message
                                error "Render deploy hook returned an error message: '${deployResponse}'. Please check Render service settings."
                            }
                            // Scenario 3: The 44-byte response is completely unknown or empty.
                            else {
                                echo "WARNING: Render deploy hook returned an unexpected 44-byte response. Assuming initiated due to HTTP 200: '${deployResponse}'"
                                // You might choose to fail here with an error, or just warn.
                            }

                        } catch (Exception e) {
                            // This catch block handles exceptions thrown by the sh command itself (e.g., command not found)
                            // or other Groovy/pipeline execution errors within the try block.
                            echo "Error executing curl command to trigger Render deployment: ${e.message}"
                            error "Pipeline failed during Render deploy hook execution. Check Jenkins connectivity, Render service status, or the exact format of the deploy hook URL."
                        }
                    }
                }
            }
        }

        stage('Run API Tests (SUT)') {
            // This stage will only run if previous stages succeed
            // You will likely have a similar setup to unit/integration tests,
            // but might require the deployed SUT to be accessible.
            steps {
                echo "Running API tests..."
                // Example: Using Newman for Postman collections
                // dir('sut-code/api-tests') {
                //     sh "newman run my_api_collection.json -e my_env.json --reporters cli,htmlextra,allure --reporter-htmlextra-export ../../newman-reports/api_report.html --reporter-allure-export ../../allure-results/api-tests"
                // }
            }
        }
    }

    post {
        always {
            script {
                echo "Publishing Consolidated Allure Report..."
                allure([
                    // Remove unknown parameters and use 'results' for the paths to raw Allure result directories
                    results: [
                        'allure-results/unit-tests',
                        'allure-results/integration-tests',
                        // If you uncomment and enable API tests, add its results path here too:
                        // 'allure-results/api-tests'
                    ]
                ]
                )
                
                echo "Consolidated Allure Report should be available via the link on the build page."

                echo "Publishing Consolidated JUnit XML Reports..."
                junit 'junit-reports/*.xml' // Collect all JUnit XML files
                echo "Consolidated JUnit Reports should be available via the 'Test Results' link."

                echo "Archiving Allure raw results and all JUnit XMLs as build artifacts..."
                archiveArtifacts artifacts: 'allure-results/**/*, junit-reports/*.xml', fingerprint: true
            }
        }
        success {
            echo "Pipeline SUCCESS. Proceeding to live deployment (if applicable)."
            // Add logic for deploying to live here, or triggering next stage/job
            // emailext (
            //     to: 'mjdwassouf@gmail.com',
            //     subject: "Jenkins Pipeline '${env.JOB_NAME}' - Build #${env.BUILD_NUMBER} SUCCESS",
            //     body: "Build successful. Check console output at: ${env.BUILD_URL}"
            // )
        }
        failure {
            echo "Pipeline FAILED. No deployment to live."
            emailext (
                to: 'mjdwassouf@gmail.com',
                subject: "Jenkins Pipeline '${env.JOB_NAME}' - Build #${env.BUILD_NUMBER} FAILED",
                body: "Build failed. Check console output at: ${env.BUILD_URL}"
            )
        }
    }
}