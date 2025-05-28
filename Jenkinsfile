pipeline {
    agent any

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
                    // Assuming Render integration uses a webhook or similar from your SCM
                    // For a simple trigger, you might just need to push to 'dev' branch
                    // which Render is already configured to deploy from.
                    // If not, you'd need Render API calls here.
                    echo "SUT automatically deployed to staging by Render on commit to ${env.SUT_BRANCH_DEV}"
                    // You might want to add a small delay to ensure Render finishes deploying
                    sleep 30 // Wait for 30 seconds for Render to deploy
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
            steps {
                dir('qa-project') {
                    sh 'pip install -r requirements.txt'
                    sh "pytest src/tests --browser chrome-headless --base-url ${env.STAGING_URL}" // Adjust pytest command as needed
                }
            }
        }

        stage('Update SUT Main and Deploy to Live') {
            when {
                expression { currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    // Checkout SUT repo again to ensure we're on the correct state for merging
                    dir('sut-main-repo') {
                        git branch: env.SUT_BRANCH_MAIN, credentials: 'YOUR_GIT_CREDENTIAL_ID', url: env.SUT_REPO
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