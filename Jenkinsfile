// Jenkinsfile for the System Under Test (SUT) repository:
// majd.kassem.business.git
// This file should be located at the root of your 'dev' branch in this repository.

pipeline {
    // Defines the Jenkins agent/node where the pipeline will run.
    // 'any' means Jenkins can use any available agent.
    agent any

    // Define external tools used by the pipeline.
    // 'M3' should match the 'Name' given to your Maven installation
    // configured in Jenkins: Manage Jenkins -> Tools -> Maven installations.
    tools {
        maven 'M3' // <<< IMPORTANT: Ensure 'M3' matches your Maven tool configuration name in Jenkins!
    }

    // Environment variables accessible throughout the pipeline.
    // These should be configured as 'Secret text' credentials in Jenkins if sensitive.
    environment {
        // --- Render Service URLs ---
        RENDER_DEV_URL = 'https://majd-kassem-business-dev.onrender.com/'
        RENDER_PROD_URL = 'https://majd-kassem-business.onrender.com/' // Included for completeness, not used in this specific pipeline.

        // --- IMPORTANT: Render Service IDs ---
        // Get these from your Render Dashboard URL for each service (e.g., srv-xxxxxxxxxxxxxxxxx).
        // These are used for triggering deployments via the Render API.
        RENDER_DEV_SERVICE_ID = 'srv-your-dev-service-id' // <<< IMPORTANT: Replace with your actual Render Dev Service ID!
        RENDER_LIVE_SERVICE_ID = 'srv-d0h686q4d50c73c6g410' // Your existing Render Live Service ID.
        
        // --- IMPORTANT: Jenkins Credential ID for Render API Key ---
        // This MUST match the ID you gave your Secret text credential in Jenkins.
        RENDER_API_KEY_CREDENTIAL_ID = 'render-api-key' // <<< IMPORTANT: Ensure this matches your Jenkins credential ID!
    }

    // Triggers define how the pipeline is started.
    triggers {
        // Poll SCM every 2 minutes.
        // This pipeline is in the SUT repo, and the Jenkins job is configured to poll this SCM.
        pollSCM('H/2 * * * *')
    }

    // Stages define the sequential steps of your pipeline.
    stages {
        // The 'Declarative: Checkout SCM' stage implicitly runs at the very beginning of the pipeline
        // because 'agent any' is at the top level and the Jenkins job is configured to use 'Pipeline script from SCM'.
        // It automatically checks out the SUT repository (majd.kassem.business.git) into the workspace root.
        // Therefore, an explicit 'Checkout SUT Code' stage is redundant if you just want to checkout the primary SCM.

        // Stage to build your System Under Test (SUT) using Maven.
        stage('Build SUT') {
            steps {
                script {
                    echo "Building the System Under Test (SUT) with Maven..."
                    // The 'mvn' command is now available in the PATH due to the 'tools' directive.
                    sh """
                    cd business/
                    $MAVEN_HOME/bin/mvn clean install
                    """
                }
            }
            // Post-actions for this specific stage.
            post {
                failure {
                    error "SUT Build Failed! Cannot proceed with deployment. ❌"
                }
            }
        }

        // Stage to deploy the built SUT to the Render Dev Service using the Render API.
        stage('Deploy to Dev Service') {
            steps {
                script {
                    echo "Triggering deployment of SUT to Render Dev Service: ${env.RENDER_DEV_URL}"
                    // 'withCredentials' securely injects the Render API Key from Jenkins credentials store.
                    withCredentials([string(credentialsId: env.RENDER_API_KEY_CREDENTIAL_ID, variable: 'RENDER_API_KEY')]) {
                        // Using Render API to trigger a deploy. Replace SERVICE_ID with your actual Dev Render Service ID.
                        sh "curl -X POST -H \"Authorization: Bearer ${RENDER_API_KEY}\" \"https://api.render.com/v1/services/${env.RENDER_DEV_SERVICE_ID}/deploys\""
                    }
                    echo "Deployment trigger sent to Render Dev! Check Render dashboard for status."
                }
            }
            // Post-actions for this specific stage.
            post {
                failure {
                    error "Failed to trigger Render Dev deployment! Please check API key, Service ID, or Render status. ❌"
                }
                success {
                    echo "Successfully triggered Render Dev deployment. 🎉"
                }
            }
        }

        // Stage to trigger the separate QA-Selenium-Pipeline job.
        // This job will then perform the actual UI tests against the deployed Dev service.
        stage('Trigger QA Tests') {
            steps {
                script {
                    echo "Triggering QA-Selenium-Pipeline job..."
                    // The 'build' step triggers another Jenkins job by its name.
                    // 'parameters' allows passing dynamic data to the triggered job.
                    // 'wait: true' ensures this pipeline pauses until the QA job completes (or fails).
                    build job: 'QA-Selenium-Pipeline',
                          parameters: [
                              string(name: 'SUT_DEV_URL', value: env.RENDER_DEV_URL), // Pass the Dev URL as a parameter.
                              string(name: 'SUT_BUILD_NUMBER', value: env.BUILD_NUMBER) // Pass the current SUT build number for traceability.
                          ],
                          wait: true // Wait for the QA job to complete before proceeding (useful for overall pipeline status).
                    echo "QA-Selenium-Pipeline job triggered and completed (or failed)."
                }
            }
            // Post-actions for this specific stage.
            post {
                failure {
                    // If the QA job fails, this pipeline will also be marked as failure.
                    error "QA-Selenium-Pipeline job FAILED! Check its console output for details. ❌"
                }
                success {
                    echo "QA-Selenium-Pipeline job completed successfully. ✅"
                }
            }
        }
    }

    // Global post-actions that run after the entire pipeline has finished, regardless of overall status.
    post {
        always {
            echo "Pipeline finished for job ${env.JOB_NAME}, build number ${env.BUILD_NUMBER}."
        }
        success {
            echo "Overall SUT-Dev-Pipeline SUCCESS: Build, Dev deploy, and QA tests all passed. 🎉"
        }
        failure {
            echo "Overall SUT-Dev-Pipeline FAILED: Check above stages for errors. ❌"
        }
        aborted {
            echo "Overall SUT-Dev-Pipeline ABORTED: Build was manually stopped. 🚫"
        }
    }
}