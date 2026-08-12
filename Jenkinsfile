pipeline {
    agent any

    environment {
        IMAGE_NAME = "job-application-manager-backend"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Build Test Image') {
            steps {
                sh 'docker build --target test -t ${IMAGE_NAME}:${IMAGE_TAG}-test .'
            }
        }

        stage('Test') {
            steps {
                sh '''
                    docker create --name test-${BUILD_NUMBER} \
                        -e PYTHONPATH=/code \
                        -e DATABASE_URL="postgresql://onlyfortest:test@localhost:5432/test" \
                        -e GROQ_API_KEY="dummy-test-key" \
                        ${IMAGE_NAME}:${IMAGE_TAG}-test \
                        pytest tests --junitxml=/code/test-results.xml

                    docker start -a test-${BUILD_NUMBER} || true
                    docker cp test-${BUILD_NUMBER}:/code/test-results.xml ./test-results.xml
                    docker rm test-${BUILD_NUMBER}
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Build Production Image') {
            steps {
                sh 'docker build --target final -t ${IMAGE_NAME}:${IMAGE_TAG} .'
            }
        }
    }

    post {
        cleanup {
            sh 'docker system prune -f || true'
        }
    }
}
