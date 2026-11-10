// Alternativa ao GitHub Pages: o Jenkins gera o site a partir do repositório
// no GitHub e publica, via rsync/SSH, em um servidor web (por exemplo, no C3SL).
//
// Pré-requisitos no Jenkins:
//   - plugins "GitHub" e "SSH Agent";
//   - job do tipo Multibranch Pipeline apontando para o repositório;
//   - credencial SSH com o ID "ccf-deploy-key" (chave do usuário de deploy);
//   - agente com python3 (>= 3.8) e rsync.
// Ajuste DEPLOY_USER, DEPLOY_HOST e DEPLOY_PATH abaixo.

pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }

  triggers {
    githubPush()   // dispara a cada push (configure o webhook do GitHub para o Jenkins)
  }

  environment {
    DEPLOY_USER = 'deploy'
    DEPLOY_HOST = 'ccf.c3sl.ufpr.br'
    DEPLOY_PATH = '/var/www/ccf'
  }

  stages {
    stage('Gerar site') {
      steps {
        sh 'python3 build.py'   // falha se houver JSON inválido ou link interno quebrado
      }
    }

    stage('Publicar') {
      when { branch 'main' }
      steps {
        sshagent(credentials: ['ccf-deploy-key']) {
          sh 'rsync -az --delete -e "ssh -o StrictHostKeyChecking=accept-new" dist/ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/"'
        }
      }
    }
  }

  post {
    success {
      archiveArtifacts artifacts: 'dist/**', fingerprint: true
    }
  }
}
