// Jenkinsfile (Declarative Pipeline)

pipeline {
    agent any // Or a specific agent if you have labels, e.g., agent { label 'my-jenkins-agent' }

    parameters {
        string(name: 'STAGING_URL_PARAM', defaultValue: 'https://majd-kassem-business-dev.onrender.com', description: 'URL of the SUT staging environment')
    }

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
        SUT_BRANCH_MAIN = 'main' // Make sure this is 'main' or whatever your production branch is called
        // You also need RENDER_DEPLOY_HOOK_URL if you're using it l
    }

    tools {
        // IMPORTANT: Ensure these tool names match exactly what you've configured in Jenkins
        nodejs 'NodeJS_24'
        allure 'Allure_2.34.0'
        // If you manage Python through Jenkins Tools, add it here, e.g.:
        // python 'Python_3.13' // Example, replace with your Python tool name if applicable
    }

    stages {
        stage('Checkout SUT Main for Merge') {
            steps {
                script {
                    echo "Checking out SUT repository: ${env.SUT_REPO}, branch: ${env.SUT_BRANCH_MAIN}"
                    // It's good to define this directory as a variable if used often
                    def mergeDir = 'sut-main-for-deploy'
                    dir(mergeDir) {
                        // Ensure a clean slate before checkout
                        cleanWs() // Cleans the workspace directory before cloning
                        git branch: env.SUT_BRANCH_MAIN, credentialsId: env.GIT_CREDENTIAL_ID, url: env.SUT_REPO
                    }
                }
            }
        }
        stage('Merge Dev to Main & Push') {
            steps {
                script {
                    def mergeDir = 'sut-main-for-deploy'
                    dir(mergeDir) {
                        echo "Configuring Git user for the merge commit..."
            
                        // Pull main to ensure it's up-to-date before merging dev
                        echo "Pulling latest ${env.SUT_BRANCH_MAIN} to ensure it's up-to-date..."
                        sh "git pull origin ${env.SUT_BRANCH_MAIN}"

                        echo "Fetching latest ${env.SUT_BRANCH_DEV} to ensure up-to-date merge..."
                        sh "git fetch origin ${env.SUT_BRANCH_DEV}"

                        echo "Merging origin/${env.SUT_BRANCH_DEV} into origin/${env.SUT_BRANCH_MAIN}..."
                        // Use --no-ff (no fast-forward) to always create a merge commit, even if it could be fast-forwarded.
                        // This keeps a clear history of merges.
                        sh "git merge --no-ff origin/${env.SUT_BRANCH_DEV} -m 'Merge ${env.SUT_BRANCH_DEV} to ${env.SUT_BRANCH_MAIN} after successful QA tests [Jenkins CI]'"

                        echo "Pushing merged ${env.SUT_BRANCH_MAIN} to remote (triggers Render live deploy)..."
                       withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIAL_ID, passwordVariable: 'GIT_PAT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
    // This is the correct and reliable way to push with a PAT now:
                            sh """
                                git config credential.helper 'cache --timeout=120'
                                echo "protocol=https\\nhost=github.com\\nusername=${GIT_USERNAME}\\npassword=${GIT_PAT_PASSWORD}" | git credential approve
                                git push origin ${env.SUT_BRANCH_MAIN}
                                # Clean up credential helper (optional, but good practice)
                                git config --unset credential.helper
                            """
                        }
                        echo "SUT Main branch updated. Render will now deploy to live."
                    }
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