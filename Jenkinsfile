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
                    dir('my_learning_platform') {
                        sh 'rm -rf ../allure-results/unit-tests' // Clear old results
                        sh 'mkdir -p ../allure-results/unit-tests'
                        sh 'mkdir -p ../junit-reports'
                        sh '''#!/bin/bash -el
                            source .venv/bin/activate
                            pytest --alluredir=../allure-results/unit-tests \\
                                   --junitxml=../junit-reports/sut_unit_report.xml \\
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
                    withCredentials([string(credentialsId: 'ENDER_DEV_DEPLOY_HOOK', variable: 'Render_Deploy_Hook_URL')]) {
                            echo "Triggering Render deployment for ${env.STAGING_URL}..."
                            // 2. TRIGGER THE DEPLOYMENT USING CURL AND THE DEPLOY HOOK URL
                            //    - This is the command that initiates a new build/deploy on Render
                            sh "curl -X POST ${Render_Deploy_Hook_URL}"
                            echo "Render deployment triggered via Deploy Hook. Waiting for it to become healthy."
                            
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