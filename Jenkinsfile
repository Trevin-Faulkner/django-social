pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "jack61318/django-app"
        TAG = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/Trevin-Faulkner/django-social.git'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'python3 -m venv venv'
                sh '. venv/bin/activate && pip install -r requirements.txt'
                sh '. venv/bin/activate && python manage.py test'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t $DOCKER_IMAGE:$TAG ."
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                      echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                      docker push $DOCKER_IMAGE:$TAG
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                      sed -i "s|:latest|:$TAG|g" k8s/deployment.yaml
                      kubectl apply -f k8s/
                    '''
                }
            }
        }
    }
}
