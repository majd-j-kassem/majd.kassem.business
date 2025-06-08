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
        JUNIT_REPORTS_ROOT = 'junit-reports'
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

                    sh "rm -rf ${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/unit-tests" // Clear old results for unit tests
                    sh "mkdir -p ${TEST_RESULT_ROOT}/${ALLURE_RESULTS_ROOT}/unit-tests" // Create directory for unit test allure results
                    sh "mkdir -p ${TEST_RESULT_ROOT}/${JUNIT_REPORTS_ROOT}" // Create the main JUnit reports directory (only needs to be done once)

                    dir('my_learning_platform') {
                        sh '''#!/bin/bash -el
                            source .venv/bin/activate
                            pytest --alluredir=../${TEST_RESULT_ROOT}/${ALLURE_RESULTS_DIR_NAME}/unit-tests \\
                           --junitxml=../${TEST_RESULT_ROOT}/${JUNIT_REPORTS_DIR_NAME}/sut_unit_report.xml \\
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
                    dir('my_learning_platform') {
                        sh 'rm -rf ../allure-results/integration-tests' // Clear old results
                        sh 'mkdir -p ../allure-results/integration-tests'
                        sh 'mkdir -p ../junit-reports' // Ensure this exists for JUnit XML if needed
                        sh '''#!/bin/bash -el
                            source .venv/bin/activate
                            pytest --alluredir=../allure-results/integration-tests \\
                                   --junitxml=../junit-reports/sut_integration_report.xml \\
                                   accounts/tests/integration/
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
                    sleep(120) // Keep your sleep for now

                    // Define the full absolute path for Newman's Allure results
                    def newmanAllureResultsAbsoluteDir = "${pwd()}/${ALLURE_RESULTS_ROOT}/api-tests"
                    // NEW: Define the full absolute path for Newman's JUnit XML report
                    def newmanJunitReportFile = "${pwd()}/${JUNIT_REPORTS_ROOT}/api_report.xml"

                    // Clean and create directory structure using the absolute path
                    sh "rm -rf ${newmanAllureResultsAbsoluteDir}"
                    sh "mkdir -p ${newmanAllureResultsAbsoluteDir}"
                    // NEW: Ensure the dedicated JUnit reports directory exists
                    sh "mkdir -p ${pwd()}/${JUNIT_REPORTS_ROOT}"

                    dir("sut-code/${env.API_TESTS_DIR}") {
                        sh """#!/bin/bash
                            echo "Current directory: \$(pwd)"
                            echo "Files in directory:"
                            ls -la

                            if [ ! -f "5_jun_env.json" ]; then
                                echo "ERROR: Environment file 5_jun_env.json not found!"
                                exit 1
                            fi

                            # --- DEBUG LINE (optional, but good for verification) ---
                            echo "--- STAGING_URL from Jenkins environment: ${env.STAGING_URL} ---"
                            # --- END DEBUG LINE ---

                            # --------------------------------------------------------------------------------
                            #  PUT THE NEWMAN_BASE_URL LOGIC HERE!
                            # --------------------------------------------------------------------------------
                            NEWMAN_BASE_URL="${env.STAGING_URL}"
                            if [[ "\$NEWMAN_BASE_URL" == */ ]]; then
                                NEWMAN_BASE_URL="\${NEWMAN_BASE_URL%/}"
                            fi
                            echo "--- Newman Base URL after processing: \$NEWMAN_BASE_URL ---" # Add this to confirm the change
                            # --------------------------------------------------------------------------------

                            newman run 5_jun_api.json \\
                                --folder "test_1" \\
                                -e 5_jun_env.json \\
                                --reporters cli,htmlextra,allure,junit \\
                                --reporter-htmlextra-export newman-report.html \\
                                --reporter-allure-export ${newmanAllureResultsAbsoluteDir} \\
                                --reporter-junit-export ${newmanJunitReportFile} \\
                                --env-var "baseUrl=\${NEWMAN_BASE_URL}" # Use the processed variable here
                        """
                    }
                }
            }
        }
    }

    post {
            always {
                script {
                    echo "Publishing Consolidated Allure Report..."
                    step([$class: 'AllureReportPublisher',
                        results: [
                            [path: 'allure-results/unit-tests'],
                            [path: 'allure-results/integration-tests']
                        ],
                        reportBuildExitCode: 0,
                        reportCharts: true
                    ])
                    echo "Consolidated Allure Report should be available via the link on the build page."

                    echo "Publishing Consolidated JUnit XML Reports..."
                    junit 'junit-reports/*.xml'
                    echo "Consolidated JUnit Reports should be available via the 'Test Results' link."

                    echo "Archiving Allure raw results and all JUnit XMLs as build artifacts..."
                    archiveArtifacts artifacts: 'allure-results/**/*', fingerprint: true
                    archiveArtifacts artifacts: 'junit-reports/*.xml', fingerprint: true
                }
            }
            // ... other post conditions if any
        }
}