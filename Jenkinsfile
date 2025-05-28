pipeline {
    agent any

    stages {
        stage('Checkout SUT Code') {
            steps {
                git branch: 'dev', url: 'https://github.com/majd-j-kassem/majd.kassem.business.git', credentialsId: 'YOUR_GIT_CREDENTIALS_ID'
            }
        }
        stage('Build SUT') {
            steps {
                sh 'mvn clean install' // Or your build command
            }
        }
        stage('Deploy to Staging') {
            steps {
                sh 'scp target/your-sut.jar user@staging-server:/opt/your-app/' // Example: Adjust for your deployment
                sh 'ssh user@staging-server "sudo systemctl restart your-sut-service"' // Example: Restart service
            }
        }
    }
    post {
        success {
            echo "SUT built and deployed to Staging successfully. Triggering QA tests..."
            build job: 'QA-Tests-Staging', wait: true
        }
        failure {
            echo "SUT build or deployment to Staging failed. Nothing deployed."
        }
    }
}