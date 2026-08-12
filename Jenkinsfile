pipeline {
    agent any

    environment {
        IMAGE_NAME = "job-application-manager-backend"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }

        stage('Test') {
            steps {
                sh '''
                    docker run --rm \
                        -v "$WORKSPACE/tests:/code/tests:ro" \
                        -v "$WORKSPACE:/results" \
                        -e PYTHONPATH=/code \
                        -e DATABASE_URL="postgresql://onlyfortest:test@localhost:5432/test" \
                        -w /code \
                        ${IMAGE_NAME}:${IMAGE_TAG} \
                        pytest tests --junitxml=/results/test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }
    }

    post {
        cleanup {
            sh 'docker system prune -f || true'
        }
    }
}
