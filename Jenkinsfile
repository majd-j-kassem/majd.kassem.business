// Jenkinsfile (Declarative Pipeline)

pipeline {
    agent any // Or a specific agent if you have labels, e.g., agent { label 'my-jenkins-agent' }

    environment {
        SUT_REPO = 'https://github.com/majd-j-kassem/majd.kassem.business.git'
        SUT_BRANCH_DEV = 'dev'
        STAGING_URL = 'https://majd-kassem-business-dev.onrender.com/' // Ensure this is your actual Render dev URL
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