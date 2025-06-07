// Corrected and Consolidated Jenkinsfile (to be placed in your SUT repo as 'Jenkinsfile')
pipeline {
    agent any // This job can run on any available Jenkins agent.
    tools {
        // Define NodeJS tool globally for the pipeline
        nodejs 'NodeJS_24'
    }

    environment {
        // Consolidated Environment Variables
        SUT_REPO = 'https://github.com/majd-j-kassem/majd.kassem.business.git'
        QA_REPO = 'https://github.com/majd-j-kassem/majd.kassem.business_qa.git'

        STAGING_URL = 'https://majd-kassem-business-dev.onrender.com' // Your Render dev URL
        LIVE_URL = 'https://majd-kassem-business.onrender.com' // Your Render live URL

        // Ensure a single credential ID variable is used for all Git checkouts
        GIT_CREDENTIAL_ID = 'git_id'

        DJANGO_SETTINGS_MODULE = 'my_learning_platform_core.settings' // Specific to SUT
        SUT_BRANCH_DEV = 'dev' // Assuming you're working on dev branch for SUT
        QA_BRANCH = 'dev' // Assuming your QA repo also has a dev branch

        STAGING_TARGET_BRANCH = 'dev'
        SUT_BRANCH_MAIN = 'main'
        API_TESTS_DIR = 'API_POSTMAN' // Assuming your Postman files are in a folder named API_POSTMAN

        // Global report directories (relative to Jenkins WORKSPACE root)
        ALLURE_ROOT_DIR = 'allure-results'
        JUNIT_ROOT_DIR = 'junit-reports'
        RENDER_SERVICE_ID_DEV = 'srv-d0pau63e5dus73dkco6g'
        // QA_JOB_NAME and LIVE_DEPLOY_JOB_NAME are no longer needed as separate jobs are integrated
        // QA_ALLURE_RESULTS_ROOT and QA_JUNIT_RESULTS_ROOT are no longer needed as they are sub-directories
    }

    stages {
        stage('Test NodeJS Tool') {
            steps {
                script {
                    echo "Attempting to use NodeJS tool..."
                    sh 'node -v' // Check if node command is available
                    sh 'npm -v'  // Check if npm command is available
                }
            }
        }

        stage('Checkout SUT Dev') {
            steps {
                script {
                    echo "Checking out SUT repository: ${SUT_REPO}, branch: ${SUT_BRANCH_DEV}"
                    dir('sut-code') { // Checkout into a dedicated directory
                        git branch: SUT_BRANCH_DEV, credentialsId: GIT_CREDENTIAL_ID, url: SUT_REPO
                    }
                }
            }
        }

        stage('Setup Python Environment (SUT)') { // Renamed for clarity
            steps {
                script {
                    echo "Setting up Python virtual environment and installing dependencies for SUT..."
                    dir('sut-code') {
                        sh 'python3 -m venv .venv'
                        sh 'bash -c "source .venv/bin/activate && pip install --upgrade pip"'
                        sh 'bash -c "source .venv/bin/activate && pip install -r requirements.txt"'
                    }
                }
            }
        }

        stage('Setup NodeJS and Newman (SUT)') { // Renamed for clarity
            steps {
                script {
                    echo "Installing Newman and Allure reporter..."
                    // This installs globally to the agent's environment where the build runs
                    sh 'npm install -g newman@latest newman-reporter-allure@latest newman-reporter-htmlextra@latest'
                    
                }
            }
        }

        stage('Run Unit Tests (SUT)') { // Renamed for clarity
            steps {
                script {
                    echo "Running Django unit tests with pytest and generating Allure and JUnit results..."
                    dir('sut-code/my_learning_platform') {
                        // CORRECTED PATHS: Use WORKSPACE directly for absolute paths from the root of the Jenkins workspace
                        def unitTestAllureResultsDir = "${WORKSPACE}/${ALLURE_ROOT_DIR}/unit-tests"
                        def unitTestJunitReportFile = "${WORKSPACE}/${JUNIT_ROOT_DIR}/sut_unit_report.xml"

                        sh "rm -rf ${unitTestAllureResultsDir}"
                        sh "mkdir -p ${unitTestAllureResultsDir}"
                        sh "mkdir -p ${WORKSPACE}/${JUNIT_ROOT_DIR}" // Ensure global JUnit reports directory exists

                        sh '''#!/bin/bash
                            # Check if the core app directory exists
                            [ -d my_learning_platform_core ] && echo "my_learning_platform_core directory found." || echo "Error: my_learning_platform_core directory NOT found."
                            source ../.venv/bin/activate
                            pytest accounts/tests/unit --alluredir=''' + unitTestAllureResultsDir + ''' --junitxml=''' + unitTestJunitReportFile + '''
                        '''
                    }
                }
            }
        }

       
        
        stage('Run Integration Tests (SUT)') { // Renamed for clarity
            steps {
                script {
                    echo "Running Django integration tests with pytest and generating Allure results..."
                    dir('sut-code/my_learning_platform') {
                        // CORRECTED PATHS: Use WORKSPACE directly for absolute paths
                        def integrationTestAllureResultsDir = "${WORKSPACE}/${ALLURE_ROOT_DIR}/integration-tests"
                        def integrationTestJunitReportFile = "${WORKSPACE}/${JUNIT_ROOT_DIR}/sut_integration_report.xml"

                        sh "rm -rf ${integrationTestAllureResultsDir}"
                        sh "mkdir -p ${integrationTestAllureResultsDir}"
                        sh "mkdir -p ${WORKSPACE}/${JUNIT_ROOT_DIR}"

                        sh '''#!/bin/bash
                            source ../.venv/bin/activate
                            pytest accounts/tests/integration \\
                                --alluredir=''' + integrationTestAllureResultsDir + ''' \\
                                --junitxml=''' + integrationTestJunitReportFile + '''
                        '''
                    }
                }
            }
        }

        stage('Build and Deploy SUT to Staging (via Render)') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    withCredentials([string(credentialsId: 'RENDER_API_TOKEN_DEV', variable: 'RENDER_AUTH_TOKEN')]) {
                        echo "Authenticating with Render API for deployment..."

                        def currentCommitSha = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                        echo "Current commit SHA for deployment: ${currentCommitSha}"

                        // Define the payload as a multi-line string
                        def deployPayload = """
                            {
                                "clearCache": true,
                                "commitId": "${currentCommitSha}"
                            }
                        """
                        echo "Triggering Render deployment for Service ID: ${RENDER_SERVICE_ID_DEV} on branch ${STAGING_TARGET_BRANCH}..."

                        def deployResponse
                        try {
                            // Write the JSON payload to a temporary file
                            writeFile(file: 'render_payload.json', text: deployPayload)
                            //=============================
                            echo "Content of render_payload.json:"
                            sh "cat render_payload.json"
                            //===============================

                            // Use the temporary file with curl -d @filename
                            deployResponse = sh(
                                script: "curl -s -X POST -H 'Authorization: Bearer ${RENDER_AUTH_TOKEN}' -H 'Content-Type: application/json' -d @render_payload.json https://api.render.com/v1/services/${RENDER_SERVICE_ID_DEV}/deploys",
                                returnStdout: true
                            ).trim()
                            echo "Render Deploy API Raw Response: ${deployResponse}"

                            // Clean up the temporary file
                            sh(script: "rm render_payload.json")

                        } catch (e) {
                            error "Failed to trigger Render deployment via API: ${e.getMessage()}"
                        }

                        def deployId
                        try {
                            def jsonResponse = readJSON(text: deployResponse)
                            deployId = jsonResponse.id
                            if (!deployId) {
                                error "Render Deploy API did not return a deployment ID. Response: ${deployResponse}"
                            }
                            echo "Render deployment triggered. New Deployment ID: ${deployId}"
                        } catch (e) {
                            error "Failed to parse Render Deploy API response or get deployment ID: ${e.getMessage()}. Response: ${deployResponse}"
                        }

                        def maxAttempts = 60
                        def retryDelaySeconds = 15
                        def attempts = 0
                        def serviceLive = false

                        echo "Starting smart wait for Render deployment (ID: ${deployId}) to become live..."

                        while (attempts < maxAttempts && !serviceLive) {
                            attempts++
                            echo "Attempt ${attempts}/${maxAttempts}: Checking Render deployment status for ID: ${deployId}..."
                            try {
                                def deployStatusJson = sh(
                                    script: "curl -s -H 'Authorization: Bearer ${RENDER_AUTH_TOKEN}' https://api.render.com/v1/services/${RENDER_SERVICE_ID_DEV}/deploys/${deployId}",
                                    returnStdout: true
                                ).trim()

                                def status = readJSON(text: deployStatusJson).status
                                echo "Deployment status for ID ${deployId}: ${status}"

                                if (status == 'live') {
                                    serviceLive = true
                                    echo "Render deployment (ID: ${deployId}) is live and healthy!"
                                } else if (status == 'failed' || status == 'canceled' || status == 'build_failed') {
                                    error "Render deployment (ID: ${deployId}) failed with status: ${status}. Failing pipeline."
                                } else {
                                    echo "Deployment not yet live. Current status: ${status}. Retrying in ${retryDelaySeconds} seconds..."
                                    sleep retryDelaySeconds
                                }
                            } catch (e) {
                                echo "Error checking deployment status for ID ${deployId}: ${e.getMessage()}. Retrying in ${retryDelaySeconds} seconds..."
                                sleep retryDelaySeconds
                            }
                        }

                        if (!serviceLive) {
                            error "Render deployment (ID: ${deployId}) did not become live within ${maxAttempts * retryDelaySeconds} seconds. Failing pipeline."
                        }

                        echo "Running final public health check on ${STAGING_URL}/health/ to confirm connectivity..."
                        def publicHealthCheckAttempts = 5
                        def publicServiceHealthy = false
                        def currentPublicAttempt = 0
                        while (currentPublicAttempt < publicHealthCheckAttempts && !publicServiceHealthy) {
                            currentPublicAttempt++
                            try {
                                def httpCode = sh(
                                    script: "curl -s -o /dev/null -w '%{http_code}' ${STAGING_URL}/health/",
                                    returnStdout: true
                                ).trim()
                                echo "Public health check HTTP status: ${httpCode}"
                                if (httpCode == '200') {
                                    publicServiceHealthy = true
                                    echo "Public health check passed for ${STAGING_URL}/health/."
                                } else {
                                    echo "Public health check failed. HTTP Code: ${httpCode}. Retrying in ${retryDelaySeconds} seconds..."
                                    sleep retryDelaySeconds
                                }
                            } catch (e) {
                                echo "Error during public health check: ${e.getMessage()}. Retrying..."
                                sleep retryDelaySeconds
                            }
                        }
                        if (!publicServiceHealthy) {
                            error "Public hlealth check on ${STAGING_URL}/health/ failed even after Render API reported live. This might indicate an issue with the service's public exposure."
                        }
                    }
                }
            }
        }
    }
        
    // --- CONSOLIDATED AND FIXED POST SECTION (ensuring emails send before deletion) ---
    post {
        always {
            script {
                echo "Publishing Consolidated Allure Report..."
                // Ensure the 'Allure_2.34.0' tool is defined globally in Jenkins or via tools{} block at pipeline level
                tool name: 'Allure_2.34.0', type: 'ru.yandex.qatools.allure.jenkins.tools.AllureCommandlineInstallation'

                allure(
                    reportBuildPolicy: 'ALWAYS',
                    includeProperties: false,
                    jdk: '',
                    properties: [],
                    results: [
                        // Paths for SUT tests
                        [path: "${ALLURE_ROOT_DIR}/unit-tests"],
                        [path: "${ALLURE_ROOT_DIR}/integration-tests"],
                        [path: "${ALLURE_ROOT_DIR}/api-tests"], // Ensure this path matches the one used in Newman
                        // Path for QA tests
                        [path: "${ALLURE_ROOT_DIR}/qa-tests"]
                    ]
                )
                echo "Consolidated Allure Report should be available via the link on the build page."

                echo "Publishing Consolidated JUnit XML Reports..."
                // This will collect all XML files from the junit-reports directory, from both SUT and QA tests
                junit "${JUNIT_ROOT_DIR}/*.xml"
                echo "Consolidated JUnit Reports should be available via the 'Test Results' link."

                echo "Archiving Allure raw results and all JUnit XMLs as build artifacts..."
                // Archive ALL raw Allure data and ALL JUnit XMLs
                archiveArtifacts artifacts: "${ALLURE_ROOT_DIR}/**,${JUNIT_ROOT_DIR}/*.xml", fingerprint: true

                // Removed problematic 'testResultAction' logic. Jenkins handles basic test stats display automatically.

                // --- NEW FIX: Email logic executed *before* deleteDir() within the 'always' block ---
                if (currentBuild.result == 'SUCCESS') {
                    echo 'Pipeline finished successfully. Deployment to Live triggered (if configured).'
                    emailext (
                        to: 'mjdwassouf@gmail.com',
                        subject: "Jenkins Pipeline SUCCESS: ${env.JOB_NAME} - Build #${env.BUILD_NUMBER}",
                        body: """
                        <p>Build Status: <b>SUCCESS</b></p>
                        <p>Project: ${env.JOB_NAME}</p>
                        <p>Build URL: <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
                        <p>Consolidated Allure Report: <a href="${env.BUILD_URL}allure/">Click here to view Allure Report</a></p>
                        <p>See attached for consolidated JUnit XML results.</p>
                        """,
                        mimeType: 'text/html',
                        attachmentsPattern: "${JUNIT_ROOT_DIR}/*.xml" // Attach all JUnit XMLs
                    )
                } else if (currentBuild.result == 'UNSTABLE') {
                    echo 'Pipeline finished with UNSTABLE tests.'
                    emailext (
                        to: 'mjdwassouf@gmail.com',
                        subject: "Jenkins Pipeline UNSTABLE: ${env.JOB_NAME} - Build #${env.BUILD_NUMBER} (Some Tests Failed)",
                        body: """
                        <p>Build Status: <b>UNSTABLE</b> (Some tests failed)</p>
                        <p>Project: ${env.JOB_NAME}</p>
                        <p>Build URL: <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
                        <p>Consolidated Allure Report: <a href="${env.BUILD_URL}allure/">Click here to view Allure Report</a></p>
                        <p>See attached for consolidated JUnit XML results.</p>
                        """,
                        mimeType: 'text/html',
                        attachmentsPattern: "${JUNIT_ROOT_DIR}/*.xml" // Attach all JUnit XMLs
                    )
                } else if (currentBuild.result == 'FAILURE') {
                    echo 'Pipeline FAILED. No deployment to live.'
                    emailext (
                        to: 'mjdwassouf@gmail.com',
                        subject: "Jenkins Pipeline FAILED: ${env.JOB_NAME} - Build #${env.BUILD_NUMBER}",
                        body: """
                        <p>Build Status: <b>FAILED!</b></p>
                        <p>Project: ${env.JOB_NAME}</p>
                        <p>Build URL: <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
                        <p>Please check the console output for details: <a href="${env.BUILD_URL}console">Console Output</a></p>
                        <p>Consolidated Allure Report (if generated): <a href="${env.BUILD_URL}allure/">Click here to view Allure Report</a></p>
                        <p>See attached for consolidated JUnit XML results (if generated).</p>
                        """,
                        mimeType: 'text/html',
                        attachmentsPattern: "${JUNIT_ROOT_DIR}/*.xml" // Attach all JUnit XMLs
                    )
                } else if (currentBuild.result == 'ABORTED') {
                    echo 'Pipeline ABORTED.'
                    // If you want an email for aborted builds, uncomment and configure it here.
                }
            }
            // --- NEW FIX: deleteDir() is the absolute LAST thing to happen in 'always' ---
            deleteDir()
        }
    }
}