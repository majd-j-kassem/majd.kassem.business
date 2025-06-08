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