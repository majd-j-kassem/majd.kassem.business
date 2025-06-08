// Jenkinsfile (Declarative Pipeline)

pipeline {
    agent any // Or a specific agent if you have labels, e.g., agent { label 'my-jenkins-agent' }

    environment {
        SUT_REPO = 'https://github.com/majd-j-kassem/majd.kassem.business.git'
        SUT_BRANCH_DEV = 'dev'
        STAGING_URL = 'https://majd-kassem-business-dev.onrender.com' // Ensure this is your actual Render dev URL
        // QA_JOB_NAME = 'QA-Tests-Staging' // REMOVED: Not triggering an external job
        GIT_CREDENTIAL_ID = 'git_id' // Unified Git credential for both repos
        DJANGO_SETTINGS_MODULE = 'my_learning_platform_core.settings'

        // Define Allure results directory relative to workspace root
        ALLURE_RESULTS_ROOT = 'allure-results'
        TEST_RESULT_ROOT = 'test-result'
        JUNIT_REPORTS_ROOT = 'junit-result'
        API_TESTS_DIR = 'API_POSTMAN' // Assuming your Postman files are in a folder named API_POSTMAN

        QA_REPO = 'https://github.com/majd-j-kassem/majd.kassem.business_qa.git'
        QA_BRANCH = 'dev'
        // LIVE_DEPLOY_JOB_NAME = 'SUT-Deploy-Live' // Keep if you use it elsewhere

        // Define QA-specific result directories (they will be inside TEST_RESULT_ROOT)
        QA_ALLURE_SUBDIR = 'qa-selenium-allure' // e.g., test-result/allure-results/qa-selenium-allure
        QA_JUNIT_SUBDIR = 'qa-selenium-junit'   // e.g., test-result/junit-result/qa-selenium-junit

        // Add explicit credential binding for Render deploy hook for clarity and security
        // Ensure 'RENDER_DEV_DEPLOY_HOOK' is configured in Jenkins Credentials as a 'Secret Text'
        RENDER_DEPLOY_HOOK_URL = credentials('RENDER_DEV_DEPLOY_HOOK')
    }

    tools {
        // IMPORTANT: Ensure these tool names match exactly what you've configured in Jenkins
        nodejs 'NodeJS_24'
        allure 'Allure_2.34.0'
        // If you manage Python through Jenkins Tools, add it here, e.g.:
        // python 'Python_3.13' // Example, replace with your Python tool name if applicable
    }

    stages {

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
                    echo "Checking out SUT repository: ${env.SUT_REPO}, branch: ${env.SUT_BRANCH_DEV}"
                    dir('sut-code') { // Checkout the SUT code into a 'sut-code' subdirectory
                        git branch: "${env.SUT_BRANCH_DEV}",
                            credentialsId: "${env.GIT_CREDENTIAL_ID}", // Using env var for credential ID
                            url: "${env.SUT_REPO}"
                    }
                }
            }
        }

        stage('Setup Python Environment (SUT)') {
            steps {
                script {
                    echo "Setting up Python virtual environment and installing dependencies for SUT..."
                    dir('my_learning_platform') { // Assuming your Python project is in 'my_learning_platform'
                        sh '''#!/bin/bash -el

                            python3 -m venv .venv
                            source .venv/bin/activate
                            pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    }
                }
            }
        }

       stage('Setup NodeJS and Newman') {
            steps {
                script {
                    echo "Installing Newman and Allure reporter..."
                    sh 'npm install -g newman newman-reporter-allure newman-reporter-htmlextra'
                }
            }
        }
        stage('Run Unit Tests (SUT)') {
            steps {
                script {
                    echo "Running Django unit tests with pytest and generating Allure and JUnit results..."

                    def unitAllureResultsDir = "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/unit-tests"
                    def unitJunitReportFile = "${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/unit_report.xml"

                    sh "rm -rf ${unitAllureResultsDir}"
                    sh "mkdir -p ${unitAllureResultsDir}"
                    sh "mkdir -p ${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}"

                    dir('my_learning_platform') {
                        sh """#!/bin/bash -el
                            source .venv/bin/activate
                            pytest --alluredir=../${unitAllureResultsDir} \\
                                   --junitxml=../${unitJunitReportFile} \\
                                   accounts/tests/unit/
                        """
                    }
                }
            }
        }
        stage('Run Integration Tests (SUT)') {
            steps {
                script {
                    echo "Running Django integration tests with pytest and generating Allure and JUnit results..."

                    def integrationAllureResultsDir = "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/integration-tests"
                    def integrationJunitReportFile = "${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/integration_report.xml"

                    sh "rm -rf ${integrationAllureResultsDir}"
                    sh "mkdir -p ${integrationAllureResultsDir}"

                     dir('my_learning_platform') {
                        sh """#!/bin/bash -el
                            source .venv/bin/activate
                            pytest --alluredir=../${integrationAllureResultsDir} \\
                                   --junitxml=../${integrationJunitReportFile} \\
                                   accounts/tests/integration/
                        """
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
                    echo "Triggering Render deployment for ${env.STAGING_URL}..."
                    // Use the environment variable directly, as it's already bound from credentials
                    sh "curl -X POST ${env.RENDER_DEPLOY_HOOK_URL}"
                    echo "Render deployment triggered via Deploy Hook. Waiting for it to become healthy."
                    sleep time: 120, unit: 'SECONDS' // Give Render time to deploy
                }
            }
        }

        stage('Run API Tests') {
            steps {
                script {
                    echo "Running Postman API tests with Newman and generating Allure and JUnit results..."

                    def allureApiResultsDir = "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/api-tests"
                    def apiJunitReportPath = "${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/api_report.xml"

                    sh "echo 'Re-initializing API Allure results directory: ${allureApiResultsDir}'"
                    sh "rm -rf ${allureApiResultsDir}"
                    sh "mkdir -p ${allureApiResultsDir}"

                    sh "echo 'Ensuring JUnit results directory exists: ${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}'"
                    sh "mkdir -p ${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}"

                    dir("${env.API_TESTS_DIR}") {
                        def newmanCommand = """#!/bin/bash -el
                            echo "Current directory inside API_POSTMAN: \$(pwd)"
                            echo "Checking for 5_jun_env.json..."
                            if [ ! -f "5_jun_env.json" ]; then
                                echo "ERROR: Environment file 5_jun_env.json not found in \$(pwd)!"
                                exit 1
                            fi
                            echo "5_jun_env.json found."

                            NEWMAN_BASE_URL="${env.STAGING_URL}"
                            if [[ "\$NEWMAN_BASE_URL" == */ ]]; then
                                NEWMAN_BASE_URL="\${NEWMAN_BASE_URL%/}"
                            fi
                            echo "NEWMAN_BASE_URL set to: \$NEWMAN_BASE_URL"

                            JUNIT_REPORT_OUTPUT="${apiJunitReportPath}"

                            echo "JUnit output path for Newman: \${JUNIT_REPORT_OUTPUT}"

                            echo "Running newman command..."
                            newman run 5_jun_api.json \\
                                --folder "test_1" \\
                                -e 5_jun_env.json \\
                                --reporters cli,htmlextra,junit \\
                                --reporter-htmlextra-export newman-report.html \\
                                --reporter-junit-export "\${JUNIT_REPORT_OUTPUT}" \\
                                --env-var "baseUrl=\${NEWMAN_BASE_URL}"

                            echo "Checking contents of JUnit output directory immediately after newman run:"
                            ls -l "\${JUNIT_REPORT_OUTPUT}"
                        """
                        sh newmanCommand
                    }

                    echo "Converting Newman's JUnit report to Allure results..."
                    sh "${tool 'Allure_2.34.0'}/bin/allure generate --clean --output ${allureApiResultsDir} ${apiJunitReportPath}"
                    echo "Checking contents of Allure API results directory after conversion:"
                    sh "ls -l ${allureApiResultsDir}"
                }
            }
        }

        stage('Run QA Tests (Selenium)') {
            when {
                // This 'when' condition means this stage will only run if previous stages were successful
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo "Starting Selenium QA tests against staging environment: ${env.STAGING_URL}"

                    // 1. Checkout QA repository into a dedicated subdirectory
                    echo "Checking out QA repository: ${env.QA_REPO}, branch: ${env.QA_BRANCH}"
                    dir('qa-selenium-project') { // Checkout QA code into 'qa-selenium-project' subdirectory
                        git branch: "${env.QA_BRANCH}",
                            credentialsId: "${env.GIT_CREDENTIAL_ID}",
                            url: "${env.QA_REPO}"
                    }

                    // 2. Setup Python Environment for QA project
                    echo "Setting up Python virtual environment and installing dependencies for QA..."
                    dir('qa-selenium-project') { // Navigate into the QA project directory
                        sh '''#!/bin/bash -el
                            python3 -m venv ./.venv
                            source ./.venv/bin/activate
                            pip install --upgrade pip
                            pip install --no-cache-dir -r requirements.txt
                        '''
                        echo "Python environment setup complete for QA."
                    }

                    // 3. Run Selenium Tests
                    echo "Running Selenium QA tests..."
                    // Define output paths for QA tests (relative to Jenkins workspace root)
                    def qaAllureOutputDir = "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/${QA_ALLURE_SUBDIR}"
                    def qaJunitReportFile = "${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/${QA_JUNIT_SUBDIR}/selenium_qa_report.xml"

                    // Create output directories
                    sh "mkdir -p ${qaAllureOutputDir}"
                    sh "mkdir -p ${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/${QA_JUNIT_SUBDIR}"

                    dir('qa-selenium-project') { // Run pytest from within the QA project directory
                        sh """#!/bin/bash -el
                            source ./.venv/bin/activate
                            # Execute pytest for Selenium tests
                            # Pass STAGING_URL to your tests. Adjust '--base-url' if your tests use a different argument.
                            # Ensure 'tests/' is the correct path to your test files within the QA repo.
                            pytest --alluredir=../${qaAllureOutputDir} \\
                                   --junitxml=../${qaJunitReportFile} \\
                                   --base-url=${env.STAGING_URL} \\
                                   src/tests/
                        """
                    }

                    // 4. (Optional) Convert QA JUnit to Allure results if pytest-allure-plugin is NOT used
                    //    If your pytest setup in the QA project is configured to generate Allure results directly
                    //    (e.g., using `pytest-allure-plugin`), this `allure generate` step might be redundant.
                    //    Check your QA project's setup. If it's not generating Allure results directly, keep this.
                    echo "Converting QA JUnit report to Allure results (if needed)..."
                    sh "${tool 'Allure_2.34.0'}/bin/allure generate --clean --output ${qaAllureOutputDir} ${qaJunitReportFile}"
                    echo "Checking contents of Allure QA results directory after conversion:"
                    sh "ls -l ${qaAllureOutputDir}"
                }
            }
        }

    } // End of stages block

    post {
        always {
            script {
                echo "---"
                echo "Starting Post-Build Actions..."
                echo "---"

                echo "Publishing Consolidated Allure Report..."
                try {
                    allure([
                        includeProperties: false,
                        jdk: '', // Leave empty if not using a specific JDK for Allure generation
                        results: [
                            [path: "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/unit-tests"],
                            [path: "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/integration-tests"],
                            [path: "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/api-tests"],
                            // --- ADD QA ALLURE RESULTS HERE ---
                            [path: "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/${QA_ALLURE_SUBDIR}"]
                        ]
                    ])
                    echo "Consolidated Allure Report should be available via the link on the build page."
                } catch (Exception e) {
                    echo "WARNING: Failed to publish Allure Report: ${e.getMessage()}"
                }

                echo "---"

                echo "Publishing Consolidated JUnit XML Reports..."
                try {
                    // Collect all JUnit XML files from all subdirectories
                    junit "${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/**/*.xml"
                    echo "Consolidated JUnit Reports should be available via the 'Test Results' link."
                } catch (Exception e) {
                    echo "WARNING: Failed to publish JUnit Reports: ${e.getMessage()}"
                }

                echo "---"

                echo "Archiving Allure raw results and all JUnit XMLs as build artifacts..."
                try {
                    // Archive all Allure raw results and all JUnit XMLs
                    archiveArtifacts artifacts: "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/**/*", fingerprint: true
                    archiveArtifacts artifacts: "${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/**/*.xml", fingerprint: true
                    echo "Test artifacts archived successfully."
                } catch (Exception e) {
                    echo "WARNING: Failed to archive build artifacts: ${e.getMessage()}"
                }

                echo "---"
                echo "Post-Build Actions Completed."
                echo "---"
            }
        }
    }
}