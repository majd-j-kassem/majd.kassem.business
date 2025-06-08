// Jenkinsfile (Declarative Pipeline)

pipeline {
    agent any // Or a specific agent if you have labels, e.g., agent { label 'my-jenkins-agent' }

    environment {
        SUT_REPO = 'https://github.com/majd-j-kassem/majd.kassem.business.git'
        SUT_BRANCH_DEV = 'dev'
        STAGING_URL = 'https://majd-kassem-business-dev.onrender.com' // Ensure this is your actual Render dev URL
        QA_JOB_NAME = 'QA-Tests-Staging'
        GIT_CREDENTIAL_ID = 'git_id'
        DJANGO_SETTINGS_MODULE = 'my_learning_platform_core.settings'

        // Define Allure results directory relative to workspace root
        ALLURE_RESULTS_ROOT = 'allure-results'
        TEST_RESULT_ROOT = 'test-result'
        JUNIT_REPORTS_ROOT = 'junit-result'
        API_TESTS_DIR = 'API_POSTMAN' // Assuming your Postman files are in a folder named API_POSTMAN

    }

    tools {
        
        nodejs 'NodeJS_24' 
        allure 'Allure_2.34.0' 
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

                    // --- These commands run from the Jenkins workspace root ---
                    // Define the full target paths for results relative to workspace root
                    def unitAllureResultsDir = "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/unit-tests"
                    def unitJunitReportFile = "${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/unit_report.xml"

                    // Clean and create directories at the workspace root
                    sh "rm -rf ${unitAllureResultsDir}"
                    sh "mkdir -p ${unitAllureResultsDir}"
                    sh "mkdir -p ${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}" // Create the JUnit root if it doesn't exist

                    // --- Now change directory to 'my_learning_platform' for running tests ---
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

                    // --- These commands run from the Jenkins workspace root ---
                    // Define the full target paths for results relative to workspace root
                    def integrationAllureResultsDir = "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/integration-tests"
                    def integrationJunitReportFile = "${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/integration_report.xml"

                    // Clean and create directories at the workspace root
                    sh "rm -rf ${integrationAllureResultsDir}"
                    sh "mkdir -p ${integrationAllureResultsDir}"
                    // The main JUnit reports directory (${TEST_RESULT_ROOT}/${JUNIT_REPORTS_DIR_NAME})
                    // should already be created by the 'Run Unit Tests (SUT)' stage,
                    // so no need to recreate it here. If this is your first test stage,
                    // you might want to add 'sh "mkdir -p ${TEST_RESULT_ROOT}/${JUNIT_REPORTS_DIR_NAME}"' here.


                    // --- Now change directory to 'my_learning_platform' for running tests ---
                     dir('my_learning_platform') {
                        sh """#!/bin/bash -el
                            source .venv/bin/activate
                            #
                            # When inside 'my_learning_platform', to reach a directory at the workspace root
                            # like 'test-results/allure-results/integration-tests', you need to go up one level (../)
                            # and then specify the path relative to the workspace root.
                            #
                            pytest --alluredir=../${integrationAllureResultsDir} \\
                                   --junitxml=../${integrationJunitReportFile} \\
                                   accounts/tests/integration/ # <--- THIS IS THE MISSING PART for integration tests
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
                    withCredentials([string(credentialsId: 'RENDER_DEV_DEPLOY_HOOK', variable: 'Render_Deploy_Hook_URL')]) {
                            echo "Triggering Render deployment for ${env.STAGING_URL}..."
                            // 2. TRIGGER THE DEPLOYMENT USING CURL AND THE DEPLOY HOOK URL
                            //    - This is the command that initiates a new build/deploy on Render
                            sh "curl -X POST ${Render_Deploy_Hook_URL}"
                            echo "Render deployment triggered via Deploy Hook. Waiting for it to become healthy."
                            
                    }
                }
            }
        }


            stage('Run API Tests') {
                steps {
                    script {
                        echo "Running Postman API tests with Newman and generating Allure and JUnit results..."
                        sleep(120) // Give Render time to deploy

                        def allureApiResultsDir = "${env.WORKSPACE}/${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/api-tests"
                        def apiJunitReportPath = "${env.WORKSPACE}/${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/api_report.xml"

                        // Clean and create directories for Allure and JUnit results
                        sh "echo 'Re-initializing API Allure results directory: ${allureApiResultsDir}'"
                        sh "rm -rf ${allureApiResultsDir}"
                        sh "mkdir -p ${allureApiResultsDir}"

                        sh "echo 'Ensuring JUnit results directory exists: ${env.WORKSPACE}/${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}'"
                        sh "mkdir -p ${env.WORKSPACE}/${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}"

                        dir("${env.WORKSPACE}/${env.API_TESTS_DIR}") {
                            // The newman command should still run with the JUnit reporter
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
                                # NOTE: Removed --reporter-allure-export as it's not working,
                                # we will convert JUnit to Allure results instead.
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

                        // --- NEW STEP: Convert Newman's JUnit report to Allure results ---
                        echo "Converting Newman's JUnit report to Allure results..."
                        sh "${tool 'Allure_2.34.0'}/bin/allure generate --clean --output ${allureApiResultsDir} ${apiJunitReportPath}"
                        echo "Checking contents of Allure API results directory after conversion:"
                        sh "ls -l ${allureApiResultsDir}"
                        // --- END NEW STEP ---
                    }
                }
            }
        
        stage('Trigger QA Tests against Staging') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo "Triggering downstream QA job: ${env.QA_JOB_NAME}"
                    // Ensure the 'STAGING_URL_PARAM' matches the parameter name in your QA-Tests-Staging job
                    build job: env.QA_JOB_NAME, parameters: [
                        string(name: 'STAGING_URL_PARAM', value: env.STAGING_URL)
                    ], wait: true
                }
            }
        }
    }
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
                    jdk: '',
                    results: [
                        [path: 'test-result/allure-results/unit-tests'],
                        [path: 'test-result/allure-results/integration-tests'],
                        [path: 'test-result/allure-results/api-tests']
                    ]
                ])
                echo "Consolidated Allure Report should be available via the link on the build page."
            } catch (Exception e) {
                echo "WARNING: Failed to publish Allure Report: ${e.getMessage()}"
            }

            echo "---"

            echo "Publishing Consolidated JUnit XML Reports..."
            try {
                junit "${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/*.xml"
                echo "Consolidated JUnit Reports should be available via the 'Test Results' link."
            } catch (Exception e) {
                echo "WARNING: Failed to publish JUnit Reports: ${e.getMessage()}"
            }

            echo "---"

            echo "Archiving Allure raw results and all JUnit XMLs as build artifacts..."
            try {
                archiveArtifacts artifacts: "${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/**/*", fingerprint: true
                archiveArtifacts artifacts: "${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}/*.xml", fingerprint: true
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