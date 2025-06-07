// Corrected and Consolidated Jenkinsfile (to be placed in your SUT repo as 'Jenkinsfile')
pipeline {
    agent any // This job can run on any available Jenkins agent.
    tools {
        // Define NodeJS tool globally for the pipeline
        nodejs 'NodeJS_24'
        // Assuming Allure Commandline is also defined globally
        // tool name: 'Allure_2.34.0', type: 'ru.yandex.qatools.allure.jenkins.tools.AllureCommandlineInstallation'
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

            stage('Setup Python Environment (SUT)') {
                steps {
                    script {
                        echo "Setting up Python virtual environment and installing dependencies for SUT..."
                        // CRITICAL CHANGE: Create the .venv inside sut-code/my_learning_platform
                        dir('sut-code/my_learning_platform') { // This aligns all Python steps
                            sh '''
                            bash -c "
                                python3 -m venv .venv
                                source .venv/bin/activate
                                pip install --upgrade pip
                                pip install -r requirements.txt
                            "
                            '''
                        }
                    }
                }
            }

            stage('Setup NodeJS and Newman (SUT)') {
                steps {
                    script {
                        echo "Installing Newman and Allure reporter..."
                        sh '''
                            # Clear npm cache (optional, but good for troubleshooting)
                            npm cache clean --force

                            # Remove the existing global node_modules directory for Newman/Allure
                            # This ensures a clean slate for the installation
                            rm -rf /var/lib/jenkins/tools/jenkins.plugins.nodejs.tools.NodeJSInstallation/NodeJS_24/lib/node_modules/newman
                            rm -rf /var/lib/jenkins/tools/jenkins.plugins.nodejs.tools.NodeJSInstallation/NodeJS_24/lib/node_modules/newman-reporter-allure
                            rm -rf /var/lib/jenkins/tools/jenkins.plugins.nodejs.tools.NodeJSInstallation/NodeJS_24/lib/node_modules/newman-reporter-htmlextra

                            # Now perform the global install
                            npm install -g newman@latest newman-reporter-allure@latest newman-reporter-htmlextra@latest
                        '''
                    }
                }
            }

            stage('Run Unit Tests (SUT)') { // Renamed for clarity and consistency
                steps {
                    script {
                        echo "Running Django unit tests with pytest and generating Allure and JUnit results..."
                        // CRITICAL CHANGE: Run unit tests from sut-code/my_learning_platform
                        dir('sut-code/my_learning_platform') {
                            // CORRECTED PATHS: Use WORKSPACE directly for absolute paths
                            def unitTestAllureResultsDir = "${WORKSPACE}/${ALLURE_ROOT_DIR}/unit-tests"
                            def unitTestJunitReportFile = "${WORKSPACE}/${JUNIT_ROOT_DIR}/sut_unit_report.xml"

                            sh "rm -rf ${unitTestAllureResultsDir}"
                            sh "mkdir -p ${unitTestAllureResultsDir}"
                            sh "mkdir -p ${WORKSPACE}/${JUNIT_ROOT_DIR}"

                            sh '''#!/bin/bash
                                source .venv/bin/activate
                                pytest \\
                                    --alluredir=''' + unitTestAllureResultsDir + ''' \\
                                    --junitxml=''' + unitTestJunitReportFile + '''
                                # No specific path needed if pytest.ini testpaths are correct,
                                # otherwise, specify e.g., accounts/tests/unit
                            '''
                        }
                    }
                }
            }

            // Kept the SECOND definition of 'Run Integration Tests (SUT)' as it was more correct
            stage('Run Integration Tests (SUT)') {
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
                                source .venv/bin/activate
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
            withCredentials([string(credentialsId: 'ENDER_DEV_DEPLOY_HOOK', variable: 'ENDER_DEPLOY_HOOK_URL')]) {
                echo "Triggering Render deployment for ${env.STAGING_URL}..."
                sh "curl -X POST ${ENDER_DEPLOY_HOOK_URL}"
                echo "Render deployment triggered via Deploy Hook. Waiting for it to become healthy."

                // Define the health check endpoint
                def healthCheckUrl = "${STAGING_URL}/health/" // Adjust if your endpoint is different

                // --- SMART HEALTH CHECK POLLING ---
                def maxRetries = 15 // Max attempts to check (e.g., 15 * 10 seconds = 150 seconds)
                def retryDelaySeconds = 10 // Delay between attempts
                def currentRetry = 0
                def serviceHealthy = false

                timeout(time: 5, unit: 'MINUTES') { // Max 5 minutes for health check
                    while (currentRetry < maxRetries && !serviceHealthy) {
                        echo "Attempt ${currentRetry + 1}/${maxRetries}: Checking service health at ${healthCheckUrl}..."
                        try {
                            // Use curl -s -o /dev/null -w "%{http_code}" to get only the HTTP status code
                            // -f (fail) added for robustness; it makes curl return an error if the server returns 4xx/5xx
                            def statusCode = sh(script: "curl -s -o /dev/null -w '%{http_code}' -f ${healthCheckUrl}", returnStdout: true).trim()
                            echo "HTTP Status Code: ${statusCode}"

                            if (statusCode == '200') {
                                serviceHealthy = true
                                echo "Service is healthy! Continuing pipeline."
                            } else {
                                echo "Service returned status ${statusCode}. Retrying in ${retryDelaySeconds} seconds..."
                                sleep retryDelaySeconds
                            }
                        } catch (Exception e) {
                            echo "Health check failed (curl error or non-200 status): ${e.message}. Retrying in ${retryDelaySeconds} seconds..."
                            sleep retryDelaySeconds
                        }
                        currentRetry++
                    }
                }

                if (!serviceHealthy) {
                    error "Service did not become healthy within the allotted time or retries. Aborting pipeline."
                }
                // --- END SMART HEALTH CHECK POLLING ---
            }
        }
    }
}
        stage('Run API Tests (SUT)') { // Renamed for clarity
            steps {
                script {
                    echo "Running Postman API tests with Newman and generating Allure and JUnit results..."
                    sleep(120) // Keep your sleep for now as a temporary measure

                        // CORRECTED PATHS: Use WORKSPACE directly for absolute paths
                    def newmanAllureResultsAbsoluteDir = "${WORKSPACE}/${ALLURE_ROOT_DIR}/api-tests"
                    def newmanJunitReportFile = "${WORKSPACE}/${JUNIT_ROOT_DIR}/sut_api_report.xml"

                    sh "rm -rf ${newmanAllureResultsAbsoluteDir}"
                    sh "mkdir -p ${newmanAllureResultsAbsoluteDir}"
                    sh "mkdir -p ${WORKSPACE}/${JUNIT_ROOT_DIR}" // Ensure global JUnit reports directory exists

                        dir("sut-code/${API_TESTS_DIR}") { // `API_TESTS_DIR` is an environment variable
                            sh """#!/bin/bash
                                echo "Current directory: \$(pwd)"
                                echo "Files in directory:"
                                ls -la

                                if [ ! -f "5_jun_env.json" ]; then
                                    echo "ERROR: Environment file 5_jun_env.json not found!"
                                    exit 1
                                fi

                                NEWMAN_BASE_URL="${STAGING_URL}"
                                if [[ "\$NEWMAN_BASE_URL" == */ ]]; then
                                    NEWMAN_BASE_URL="\${NEWMAN_BASE_URL%/}"
                                fi
                                echo "--- Newman Base URL after processing: \$NEWMAN_BASE_URL ---"

                                newman run 5_jun_api.json \\
                                    --folder "test_1" \\
                                    -e 5_jun_env.json \\
                                    --reporters cli,htmlextra,allure,junit \\
                                    --reporter-htmlextra-export newman-report.html \\
                                    --reporter-allure-export ${newmanAllureResultsAbsoluteDir} \\
                                    --reporter-junit-export ${newmanJunitReportFile} \\
                                    --env-var "baseUrl=\${NEWMAN_BASE_URL}"
                            """
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
                        // Path for QA tests (if applicable, uncomment if you add a QA test stage)
                        // [path: "${ALLURE_ROOT_DIR}/qa-tests"]
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