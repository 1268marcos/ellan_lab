// 01_source/frontend/src/pages/public/PublicPrivacyPolicyPage.jsx
// UX Mobile-First
// Acessibilidade WCAG AA
// SEO otimizado
// Data de atualização automática
import React from "react";
import { Link } from "react-router-dom";

export default function PublicPrivacyPolicyPage() {
  const lastUpdated = "15 de Março de 2024";

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        {/* Header com gradiente */}
        <div style={headerStyle}>
          <div style={headerContentStyle}>
            <span style={badgeStyle}>📋 Política de Privacidade</span>
            <h1 style={titleStyle}>Como protegemos seus dados</h1>
            <p style={subtitleStyle}>
              A sua privacidade é importante para nós. Conheça nossas práticas de coleta, 
              uso e proteção das suas informações pessoais.
            </p>
            <div style={metaInfoStyle}>
              <span>🕒 Última atualização: {lastUpdated}</span>
              <span>📌 Versão 2.0</span>
            </div>
          </div>
        </div>

        {/* Conteúdo Principal */}
        <div style={contentStyle}>
          {/* Índice rápido */}
          <div style={indexStyle}>
            <h3 style={indexTitleStyle}>Navegação rápida</h3>
            <ul style={indexListStyle}>
              <li><a href="#coleta-dados">📊 Coleta de Dados</a></li>
              <li><a href="#uso-dados">🎯 Uso das Informações</a></li>
              <li><a href="#compartilhamento">🤝 Compartilhamento</a></li>
              <li><a href="#seguranca">🔒 Segurança</a></li>
              <li><a href="#direitos">⚖️ Seus Direitos</a></li>
              <li><a href="#cookies">🍪 Cookies</a></li>
              <li><a href="#contato">📞 Contato</a></li>
            </ul>
          </div>

          {/* Seções de Conteúdo */}
          <div style={sectionsStyle}>
            <section id="coleta-dados" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>📊 1. Coleta de Dados</h2>
              <p style={paragraphStyle}>
                Coletamos informações necessárias para fornecer nossos serviços de forma adequada e segura. 
                Os dados coletados incluem:
              </p>
              <ul style={listStyle}>
                <li><strong>Dados de identificação:</strong> Nome completo, CPF/CNPJ, e-mail, telefone</li>
                <li><strong>Dados de endereço:</strong> Endereço residencial e comercial para entrega</li>
                <li><strong>Dados de pagamento:</strong> Informações de cartão de crédito, PIX e outros métodos (processados de forma segura por parceiros)</li>
                <li><strong>Dados de navegação:</strong> IP, tipo de dispositivo, navegador, páginas visitadas</li>
                <li><strong>Dados de transação:</strong> Histórico de compras, pedidos e retiradas</li>
                <li><strong>Dados de localização:</strong> Aproximada para disponibilizar lockers próximos</li>
              </ul>
              <div style={infoBoxStyle}>
                <strong>🔐 Importante:</strong> Dados sensíveis como senhas e informações de pagamento são criptografados 
                e nunca armazenados em texto plano.
              </div>
            </section>

            <section id="uso-dados" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>🎯 2. Uso das Informações</h2>
              <p style={paragraphStyle}>
                Utilizamos seus dados para:
              </p>
              <ul style={listStyle}>
                <li>✓ Processar e entregar seus pedidos</li>
                <li>✓ Enviar atualizações sobre o status do pedido</li>
                <li>✓ Melhorar nossa plataforma e experiência do usuário</li>
                <li>✓ Oferecer suporte ao cliente</li>
                <li>✓ Prevenir fraudes e atividades suspeitas</li>
                <li>✓ Cumprir obrigações legais e regulatórias</li>
                <li>✓ Enviar comunicações promocionais (com seu consentimento)</li>
              </ul>
            </section>

            <section id="compartilhamento" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>🤝 3. Compartilhamento de Dados</h2>
              <p style={paragraphStyle}>
                Seus dados podem ser compartilhados com:
              </p>
              <ul style={listStyle}>
                <li><strong>Parceiros de pagamento:</strong> Para processar transações financeiras</li>
                <li><strong>Operadoras de lockers:</strong> Para gerenciar a retirada dos produtos</li>
                <li><strong>Autoridades legais:</strong> Quando exigido por lei ou ordem judicial</li>
                <li><strong>Provedores de serviços:</strong> Como hospedagem, análise de dados e suporte técnico</li>
              </ul>
              <p style={paragraphStyle}>
                Nunca vendemos seus dados pessoais para terceiros. Qualquer compartilhamento é feito 
                estritamente para a operação dos serviços e sempre com compromissos de confidencialidade.
              </p>
            </section>

            <section id="seguranca" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>🔒 4. Segurança dos Dados</h2>
              <p style={paragraphStyle}>
                Implementamos medidas de segurança rigorosas para proteger suas informações:
              </p>
              <div style={gridStyle}>
                <div style={securityCardStyle}>
                  <span style={securityIconStyle}>🔐</span>
                  <strong>Criptografia SSL/TLS</strong>
                  <p>Todos os dados transmitidos são criptografados</p>
                </div>
                <div style={securityCardStyle}>
                  <span style={securityIconStyle}>🛡️</span>
                  <strong>Firewalls Avançados</strong>
                  <p>Proteção contra acessos não autorizados</p>
                </div>
                <div style={securityCardStyle}>
                  <span style={securityIconStyle}>🔑</span>
                  <strong>Controle de Acesso</strong>
                  <p>Acesso restrito a dados por funcionários autorizados</p>
                </div>
                <div style={securityCardStyle}>
                  <span style={securityIconStyle}>📊</span>
                  <strong>Monitoramento 24/7</strong>
                  <p>Detecção e resposta a ameaças em tempo real</p>
                </div>
              </div>
            </section>

            <section id="direitos" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>⚖️ 5. Seus Direitos</h2>
              <p style={paragraphStyle}>
                De acordo com a LGPD (Lei Geral de Proteção de Dados), você tem direito a:
              </p>
              <ul style={listStyle}>
                <li>✓ Confirmar a existência de tratamento de seus dados</li>
                <li>✓ Acessar seus dados pessoais</li>
                <li>✓ Corrigir dados incompletos, inexatos ou desatualizados</li>
                <li>✓ Solicitar a anonimização, bloqueio ou eliminação de dados desnecessários</li>
                <li>✓ Solicitar a portabilidade dos dados a outro fornecedor</li>
                <li>✓ Revogar o consentimento a qualquer momento</li>
              </ul>
              <div style={contactBoxStyle}>
                <strong>📧 Para exercer seus direitos, entre em contato:</strong>
                <a href="mailto:privacidade@ellan.pt" style={contactLinkStyle}>
                  privacidade@ellan.pt
                </a>
              </div>
            </section>

            <section id="cookies" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>🍪 6. Cookies e Tecnologias</h2>
              <p style={paragraphStyle}>
                Utilizamos cookies para melhorar sua experiência:
              </p>
              <ul style={listStyle}>
                <li><strong>Cookies Essenciais:</strong> Necessários para o funcionamento do site</li>
                <li><strong>Cookies de Desempenho:</strong> Analisam como você usa o site</li>
                <li><strong>Cookies de Funcionalidade:</strong> Lembram suas preferências</li>
                <li><strong>Cookies de Marketing:</strong> Personalizam conteúdo e anúncios (com consentimento)</li>
              </ul>
              <p style={paragraphStyle}>
                Você pode gerenciar suas preferências de cookies a qualquer momento através das 
                configurações do seu navegador.
              </p>
            </section>

            <section id="contato" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>📞 7. Contato do Encarregado</h2>
              <p style={paragraphStyle}>
                Para questões sobre privacidade ou para exercer seus direitos, entre em contato com 
                nosso Encarregado de Proteção de Dados (DPO):
              </p>
              <div style={contactInfoStyle}>
                <div><strong>📧 E-mail:</strong> dpo@ellan.pt</div>
                <div><strong>📞 Telefone:</strong> +351 253 079 738 PT</div>
                <div><strong>📬 Endereço:</strong> Av. dos Autonomistas, 1234 - Osasco, SP - CEP: 06000-000</div>
                <div><strong>⏰ Horário:</strong> Segunda a Sexta, 9h às 18h</div>
              </div>
            </section>
          </div>

          {/* Rodapé com aceitação */}
          <div style={acceptanceBoxStyle}>
            <p style={acceptanceTextStyle}>
              Ao utilizar nossos serviços, você concorda com os termos desta Política de Privacidade. 
              Esta política é revisada periodicamente e atualizações serão comunicadas por e-mail.
            </p>
          </div>
        </div>

        {/* Botões de navegação */}
        <div style={navigationButtonsStyle}>
          <Link to="/termos" style={secondaryButtonStyle}>
            📜 Ver Termos de Uso
          </Link>
          <Link to="/" style={primaryButtonStyle}>
            ← Voltar para o início
          </Link>
        </div>
      </div>

      {/* CSS Animations */}
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        section {
          animation: fadeInUp 0.5s ease-out;
        }
        
        section:nth-child(1) { animation-delay: 0.1s; }
        section:nth-child(2) { animation-delay: 0.2s; }
        section:nth-child(3) { animation-delay: 0.3s; }
        section:nth-child(4) { animation-delay: 0.4s; }
        section:nth-child(5) { animation-delay: 0.5s; }
        section:nth-child(6) { animation-delay: 0.6s; }
        section:nth-child(7) { animation-delay: 0.7s; }
        
        html {
          scroll-behavior: smooth;
        }
        
        @media (max-width: 768px) {
          .security-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </main>
  );
}

// Estilos
const pageStyle = {
  minHeight: '100vh',
  background: 'linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%)',
  padding: 'var(--spacing-4) 0'
};

const containerStyle = {
  maxWidth: '1000px',
  margin: '0 auto',
  padding: '0 var(--spacing-4)'
};

const headerStyle = {
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  borderRadius: 'var(--radius-2xl)',
  padding: 'var(--spacing-8)',
  marginBottom: 'var(--spacing-6)',
  color: 'white',
  textAlign: 'center'
};

const headerContentStyle = {
  maxWidth: '800px',
  margin: '0 auto'
};

const badgeStyle = {
  display: 'inline-block',
  padding: 'var(--spacing-1) var(--spacing-3)',
  background: 'rgba(255,255,255,0.2)',
  borderRadius: 'var(--radius-full)',
  fontSize: 'var(--font-size-sm)',
  fontWeight: 600,
  marginBottom: 'var(--spacing-3)'
};

const titleStyle = {
  fontSize: 'var(--font-size-4xl)',
  fontWeight: 800,
  marginBottom: 'var(--spacing-3)',
  lineHeight: 1.2
};

const subtitleStyle = {
  fontSize: 'var(--font-size-lg)',
  opacity: 0.95,
  lineHeight: 1.6,
  marginBottom: 'var(--spacing-4)'
};

const metaInfoStyle = {
  display: 'flex',
  justifyContent: 'center',
  gap: 'var(--spacing-4)',
  fontSize: 'var(--font-size-sm)',
  opacity: 0.9,
  flexWrap: 'wrap'
};

const contentStyle = {
  background: 'white',
  borderRadius: 'var(--radius-2xl)',
  padding: 'var(--spacing-8)',
  marginBottom: 'var(--spacing-6)',
  boxShadow: 'var(--shadow-md)'
};

const indexStyle = {
  background: '#f7fafc',
  borderRadius: 'var(--radius-lg)',
  padding: 'var(--spacing-4)',
  marginBottom: 'var(--spacing-6)',
  border: '1px solid #e2e8f0'
};

const indexTitleStyle = {
  fontSize: 'var(--font-size-base)',
  fontWeight: 700,
  marginBottom: 'var(--spacing-2)',
  color: '#2d3748'
};

const indexListStyle = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 'var(--spacing-2)',
  listStyle: 'none',
  padding: 0,
  margin: 0
};

const sectionsStyle = {
  display: 'grid',
  gap: 'var(--spacing-6)'
};

const sectionStyle = {
  scrollMarginTop: 'var(--spacing-8)'
};

const sectionTitleStyle = {
  fontSize: 'var(--font-size-2xl)',
  fontWeight: 700,
  color: '#2d3748',
  marginBottom: 'var(--spacing-3)',
  paddingBottom: 'var(--spacing-2)',
  borderBottom: '2px solid #e2e8f0'
};

const paragraphStyle = {
  fontSize: 'var(--font-size-base)',
  lineHeight: 1.6,
  color: '#4a5568',
  marginBottom: 'var(--spacing-3)'
};

const listStyle = {
  margin: 'var(--spacing-3) 0',
  paddingLeft: 'var(--spacing-5)',
  fontSize: 'var(--font-size-base)',
  lineHeight: 1.6,
  color: '#4a5568'
};

const infoBoxStyle = {
  background: '#fef3c7',
  borderLeft: '4px solid #f59e0b',
  padding: 'var(--spacing-3)',
  borderRadius: 'var(--radius-md)',
  marginTop: 'var(--spacing-3)',
  fontSize: 'var(--font-size-sm)',
  color: '#92400e'
};

const gridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
  gap: 'var(--spacing-3)',
  marginTop: 'var(--spacing-3)'
};

const securityCardStyle = {
  padding: 'var(--spacing-3)',
  background: '#f7fafc',
  borderRadius: 'var(--radius-lg)',
  textAlign: 'center'
};

const securityIconStyle = {
  fontSize: '32px',
  display: 'block',
  marginBottom: 'var(--spacing-2)'
};

const contactBoxStyle = {
  background: '#e0f2fe',
  borderLeft: '4px solid #0284c7',
  padding: 'var(--spacing-3)',
  borderRadius: 'var(--radius-md)',
  marginTop: 'var(--spacing-3)'
};

const contactLinkStyle = {
  display: 'block',
  marginTop: 'var(--spacing-2)',
  color: '#0284c7',
  fontWeight: 600,
  textDecoration: 'none'
};

const contactInfoStyle = {
  background: '#f7fafc',
  borderRadius: 'var(--radius-lg)',
  padding: 'var(--spacing-4)',
  marginTop: 'var(--spacing-3)',
  display: 'grid',
  gap: 'var(--spacing-2)'
};

const acceptanceBoxStyle = {
  marginTop: 'var(--spacing-6)',
  padding: 'var(--spacing-4)',
  background: '#f0fdf4',
  borderRadius: 'var(--radius-lg)',
  border: '1px solid #bbf7d0',
  textAlign: 'center'
};

const acceptanceTextStyle = {
  margin: 0,
  fontSize: 'var(--font-size-sm)',
  color: '#166534'
};

const navigationButtonsStyle = {
  display: 'flex',
  gap: 'var(--spacing-3)',
  justifyContent: 'center',
  flexWrap: 'wrap'
};

const primaryButtonStyle = {
  padding: 'var(--spacing-3) var(--spacing-6)',
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  color: 'white',
  textDecoration: 'none',
  borderRadius: 'var(--radius-md)',
  fontWeight: 600,
  transition: 'all var(--transition-base)',
  display: 'inline-block'
};

const secondaryButtonStyle = {
  padding: 'var(--spacing-3) var(--spacing-6)',
  background: 'white',
  color: '#667eea',
  textDecoration: 'none',
  borderRadius: 'var(--radius-md)',
  fontWeight: 600,
  border: '2px solid #667eea',
  transition: 'all var(--transition-base)',
  display: 'inline-block'
};