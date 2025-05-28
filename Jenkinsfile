pipeline {
    agent any // This means the entire pipeline runs on any available Jenkins agent.
              // We'll use a Docker agent for the specific Python-dependent stage.

    environment {
        SUT_REPO = 'https://github.com/majd-j-kassem/majd.kassem.business.git'
        QA_REPO = 'https://github.com/majd-j-kassem/majd.kassem.business_qa.git'
        SUT_BRANCH_DEV = 'dev'
        SUT_BRANCH_MAIN = 'main'
        QA_BRANCH = 'main'
        STAGING_URL = 'https://majd-kassem-business-dev.onrender.com/'
        LIVE_URL = 'https://majd-kassem-business.onrender.com/'
    }

    stages {
        stage('Checkout SUT Dev') {
            steps {
                git branch: env.SUT_BRANCH_DEV, credentialsId: 'git_id', url: env.SUT_REPO
            }
        }

        stage('Build and Deploy SUT to Staging') {
            steps {
                script {
                    echo "SUT automatically deployed to staging by Render on commit to ${env.SUT_BRANCH_DEV}"
                    // Wait for Render to finish deploying. You might adjust this based on Render's typical deployment time.
                    sleep 30
                }
            }
        }

        stage('Checkout QA Main') {
            steps {
                dir('qa-project') {
                    git branch: env.QA_BRANCH, credentialsId: 'git_id', url: env.QA_REPO
                }
            }
        }

        stage('Run QA Tests against Staging') {
            agent { // <--- This ensures this stage runs inside a Docker container with Python.
                docker {
                    image 'python:3.9-slim-buster' // A lightweight Python image.
                    args '-u root' // This can help with permissions inside the container.
                }
            }
            steps {
                dir('qa-project') {
                    // Use 'python -m pip' for robustness in Docker.
                    sh 'python -m pip install --no-cache-dir -r requirements.txt'
                    // Your pytest command. Ensure your QA project has 'pytest' installed via requirements.txt.
                    sh "pytest src/tests --browser chrome-headless --base-url ${env.STAGING_URL}"
                }
            }
        }

        stage('Update SUT Main and Deploy to Live') {
            when {
                expression { currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    // Checkout SUT repo again to ensure we're on the correct state for merging.
                    // This 'git_id' should be the same as used in other git steps.
                    dir('sut-main-repo') {
                        git branch: env.SUT_BRANCH_MAIN, credentialsId: 'git_id', url: env.SUT_REPO
                        sh "git config user.email 'jenkins@example.com'"
                        sh "git config user.name 'Jenkins'"
                        sh "git merge ${env.SUT_BRANCH_DEV} -m 'Merge dev to main after successful QA tests'"
                        sh "git push origin ${env.SUT_BRANCH_MAIN}"
                        echo "SUT Main branch updated and deployed to live by Render."
                    }
                }
            }
        }
    }

    post {
        failure {
            echo 'Pipeline failed. No deployment to live.'
        }
        success {
            echo 'Pipeline succeeded. Live deployment triggered.'
        }
    }
}