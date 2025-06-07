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
        SUT_BRANCH_MAIN = 'main'
        API_TESTS_DIR = 'API_POSTMAN' // Assuming your Postman files are in a folder named API_POSTMAN

        // Global report directories (relative to Jenkins WORKSPACE root)
        ALLURE_ROOT_DIR = 'allure-results'
        JUNIT_ROOT_DIR = 'junit-reports'

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
                    sh 'npm install -g newman newman-reporter-allure newman-reporter-htmlextra'
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
                // This condition means it will run if previous stages were successful or skipped (e.g. initial build)
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    withCredentials([string(credentialsId: 'ENDER_DEV_DEPLOY_HOOK', variable: 'ENDER_DEPLOY_HOOK_URL')]) {
                        echo "Triggering Render deployment for ${STAGING_URL}..."
                        sh "curl -X POST ${ENDER_DEPLOY_HOOK_URL}"
                        echo "Render deployment triggered via Deploy Hook."

                        // --- START Smart Wait Implementation for Staging Deployment ---
                        def maxAttempts = 20 // Max number of times to check (e.g., 20 * 15 seconds = 5 minutes)
                        def retryDelaySeconds = 15 // Seconds to wait between checks
                        def healthCheckUrl = "${STAGING_URL}/health/" // Use the STAGING URL here!
                                                                    // Ensure STAGING_URL is defined in your environment block.
                                                               // Ensure your Django app exposes '/health/' endpoint on staging.
                        def attempts = 0
                        def serviceHealthy = false

                        echo "Starting smart wait for staging service at ${healthCheckUrl} to become healthy..."

                        while (attempts < maxAttempts && !serviceHealthy) {
                            attempts++
                            echo "Attempt ${attempts}/${maxAttempts}: Checking staging service health..."
                            try {
                                // Use curl with -s (silent), -o /dev/null (discard output), -w "%{http_code}" (write HTTP code)
                                def httpCode = sh(
                                    script: "curl -s -o /dev/null -w '%{http_code}' ${healthCheckUrl}",
                                    returnStdout: true
                                ).trim()

                                echo "Received HTTP status code: ${httpCode}"

                                if (httpCode == '200') {
                                    serviceHealthy = true
                                    echo "Staging service at ${healthCheckUrl} is healthy!"
                                } else {
                                    echo "Staging service not yet healthy. Retrying in ${retryDelaySeconds} seconds..."
                                    sleep retryDelaySeconds
                                }
                            } catch (e) {
                                echo "Error checking health: ${e.getMessage()}. Retrying in ${retryDelaySeconds} seconds..."
                                sleep retryDelaySeconds
                            }
                        }

                        if (!serviceHealthy) {
                            error "Staging service at ${healthCheckUrl} did not become healthy within ${maxAttempts * retryDelaySeconds} seconds. Failing pipeline."
                        }
                        // --- END Smart Wait Implementation ---
                    } // End of withCredentials block
                } // End of script block
            } // End of steps block
        }
        stage('Run API Tests (SUT)') { // Renamed for clarity
            steps {
                script {
                    echo "Running Postman API tests with Newman and generating Allure and JUnit results..."
                     // The comment "Keep your sleep for now as a temporary measure" can be removed as the sleep is gone and smart wait is in place

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

        // --- Integrated QA Stages (from your old 'Jenkinsfile.qa_tests') ---
        stage('Checkout QA Test Code') {
            steps {
                script {
                    echo "Checking out QA repository: ${QA_REPO}, branch: ${QA_BRANCH}"
                    dir('qa-code') { // Checkout into a dedicated directory
                        git branch: QA_BRANCH, credentialsId: GIT_CREDENTIAL_ID, url: QA_REPO
                    }
                }
            }
        }

        stage('Setup Python Environment (QA)') {
            steps {
                script {
                    echo "Setting up Python virtual environment and installing dependencies for QA tests..."
                    dir('qa-code') {
                        sh 'python3 -m venv ./.venv'
                        sh 'bash -c ". ./.venv/bin/activate && pip install --no-cache-dir -r requirements.txt"'
                    }
                }
            }
        }

        stage('Run QA Tests against Staging') {
            steps {
                script {
                    echo "Running Selenium tests against Staging URL: ${STAGING_URL}"
                    dir('qa-code') {
                        // CORRECTED PATHS: Use WORKSPACE directly for absolute paths
                        def qaTestAllureResultsDir = "${WORKSPACE}/${ALLURE_ROOT_DIR}/qa-tests"
                        def qaTestJunitReportFile = "${WORKSPACE}/${JUNIT_ROOT_DIR}/qa_report.xml"

                        sh "rm -rf ${qaTestAllureResultsDir}"
                        sh "mkdir -p ${qaTestAllureResultsDir}"
                        sh "mkdir -p ${WORKSPACE}/${JUNIT_ROOT_DIR}" // Ensure global JUnit reports directory exists

                        sh """#!/bin/bash
                            . ./.venv/bin/activate
                            pytest src/tests/teachers/test_teacher_signup.py --alluredir=${qaTestAllureResultsDir} --junitxml=${qaTestJunitReportFile} --browser chrome-headless --baseurl ${STAGING_URL}
                        """
                    }
                }
            }
        }

        // --- Simplified Live Deployment Stage (relies on Git push) ---
        stage('Merge Dev to Main & Push (and Trigger Live Deploy)') { // Renamed for clarity
            when {
                // This condition ensures this critical stage only runs if the entire pipeline is successful
                expression { currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    dir('sut-code') {
                        echo "Checking out SUT Main branch for merge operation..."
                        git branch: env.SUT_BRANCH_MAIN, credentialsId: env.GIT_CREDENTIAL_ID, url: env.SUT_REPO

                        echo "Configuring Git user for the merge commit..."
                        sh "git config user.email 'jenkins@example.com'"
                        sh "git config user.name 'Jenkins CI Automation'"

                        echo "Fetching latest ${env.SUT_BRANCH_DEV} to ensure up-to-date merge..."
                        sh "git fetch origin ${env.SUT_BRANCH_DEV}" // Fetch the dev branch as well

                        echo "Merging origin/${env.SUT_BRANCH_DEV} into ${env.SUT_BRANCH_MAIN}..."
                        // Use '--no-edit' to prevent Git from opening an editor for the merge commit message.
                        // `--no-ff` ensures a merge commit is always created, useful for history.
                        sh "git merge origin/${env.SUT_BRANCH_DEV} --no-ff --commit --no-edit -m 'Merge ${env.SUT_BRANCH_DEV} to ${env.SUT_BRANCH_MAIN} after successful QA tests [Jenkins CI]'"

                        echo "Pushing merged ${env.SUT_BRANCH_MAIN} to remote. This will trigger Render live deploy."
                        withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIAL_ID, passwordVariable: 'GIT_PAT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
                            sh "git push https://${GIT_USERNAME}:${GIT_PAT_PASSWORD}@github.com/majd-j-kassem/majd.kassem.business.git ${env.SUT_BRANCH_MAIN}"
                        }
                        echo "SUT Main branch updated. Render will now deploy to live."

                        // --- START Smart Wait Implementation for Live Deployment ---
                        def maxAttempts = 20 // Max number of times to check (e.g., 20 * 15 seconds = 5 minutes)
                        def retryDelaySeconds = 15 // Seconds to wait between checks
                        // --- FIX: Corrected variable name from SUT_LIVE_URL to LIVE_URL ---
                        def healthCheckUrl = "${env.LIVE_URL}/health/" // Use the LIVE URL here!
                        def attempts = 0
                        def serviceHealthy = false

                        echo "Starting smart wait for live service at ${healthCheckUrl} to become healthy..."

                        while (attempts < maxAttempts && !serviceHealthy) {
                            attempts++
                            echo "Attempt ${attempts}/${maxAttempts}: Checking live service health..."
                            try {
                                // Use curl with -s (silent), -o /dev/null (discard output), -w "%{http_code}" (write HTTP code)
                                def httpCode = sh(
                                    script: "curl -s -o /dev/null -w '%{http_code}' ${healthCheckUrl}",
                                    returnStdout: true
                                ).trim()

                                echo "Received HTTP status code: ${httpCode}"

                                if (httpCode == '200') {
                                    serviceHealthy = true
                                    echo "Live service at ${healthCheckUrl} is healthy!"
                                } else {
                                    echo "Live service not yet healthy. Retrying in ${retryDelaySeconds} seconds..."
                                    sleep retryDelaySeconds
                                }
                            } catch (e) {
                                echo "Error checking health: ${e.getMessage()}. Retrying in ${retryDelaySeconds} seconds..."
                                sleep retryDelaySeconds
                            }
                        }

                        if (!serviceHealthy) {
                            error "Live service at ${healthCheckUrl} did not become healthy within ${maxAttempts * retryDelaySeconds} seconds. Failing pipeline."
                        }
                        // --- END Smart Wait Implementation ---
                    } // End of dir('sut-code')
                } // End of script block
            } // End of steps block
        } // End of stage block
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