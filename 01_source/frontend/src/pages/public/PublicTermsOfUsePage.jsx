// 01_source/frontend/src/pages/public/PublicTermsOfUsePage.jsx
// UX Mobile-First
// Acessibilidade WCAG AA
// SEO otimizado
import React from "react";
import { Link } from "react-router-dom";

export default function PublicTermsOfUsePage() {
  const lastUpdated = "15 de Março de 2024";

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        {/* Header */}
        <div style={headerStyle}>
          <div style={headerContentStyle}>
            <span style={badgeStyle}>📜 Termos de Uso</span>
            <h1 style={titleStyle}>Termos e Condições Gerais</h1>
            <p style={subtitleStyle}>
              Leia atentamente os termos que regem o uso da plataforma ELLAN Lab Locker.
              Ao utilizar nossos serviços, você concorda com todas as condições aqui estabelecidas.
            </p>
            <div style={metaInfoStyle}>
              <span>🕒 Última atualização: {lastUpdated}</span>
              <span>📌 Versão 2.0</span>
            </div>
          </div>
        </div>

        {/* Conteúdo */}
        <div style={contentStyle}>
          {/* Índice */}
          <div style={indexStyle}>
            <h3 style={indexTitleStyle}>Navegação rápida</h3>
            <ul style={indexListStyle}>
              <li><a href="#aceitacao">✅ Aceitação dos Termos</a></li>
              <li><a href="#servicos">🛒 Serviços Oferecidos</a></li>
              <li><a href="#cadastro">👤 Cadastro e Conta</a></li>
              <li><a href="#compras">💳 Compras e Pagamentos</a></li>
              <li><a href="#retirada">📦 Retirada de Produtos</a></li>
              <li><a href="#devolucao">🔄 Devoluções e Reembolsos</a></li>
              <li><a href="#responsabilidades">⚖️ Responsabilidades</a></li>
              <li><a href="#cancelamento">❌ Cancelamento e Suspensão</a></li>
              <li><a href="#propriedade">©️ Propriedade Intelectual</a></li>
              <li><a href="#alteracoes">🔄 Alterações nos Termos</a></li>
            </ul>
          </div>

          <div style={sectionsStyle}>
            <section id="aceitacao" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>✅ 1. Aceitação dos Termos</h2>
              <p style={paragraphStyle}>
                Ao acessar ou utilizar a plataforma ELLAN Lab Locker, você declara ter lido, 
                compreendido e concordado com todos os termos e condições estabelecidos neste documento. 
                Se você não concordar com qualquer parte destes termos, não utilize nossos serviços.
              </p>
            </section>

            <section id="servicos" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>🛒 2. Serviços Oferecidos</h2>
              <p style={paragraphStyle}>
                A ELLAN Lab Locker oferece uma plataforma de comércio eletrônico que permite:
              </p>
              <ul style={listStyle}>
                <li>✓ Compra de produtos pré-selecionados disponíveis em lockers</li>
                <li>✓ Retirada automatizada em lockers físicos</li>
                <li>✓ Acompanhamento de pedidos em tempo real</li>
                <li>✓ Emissão de comprovantes fiscais</li>
                <li>✓ Suporte ao cliente</li>
              </ul>
              <div style={warningBoxStyle}>
                <strong>⚠️ Importante:</strong> Os produtos disponíveis em cada locker são pré-configurados 
                e podem variar conforme a localização e disponibilidade de estoque.
              </div>
            </section>

            <section id="cadastro" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>👤 3. Cadastro e Conta</h2>
              <p style={paragraphStyle}>
                Para realizar compras, é necessário criar uma conta. Você se compromete a:
              </p>
              <ul style={listStyle}>
                <li>✓ Fornecer informações verdadeiras, precisas e atualizadas</li>
                <li>✓ Manter a confidencialidade de sua senha</li>
                <li>✓ Notificar imediatamente qualquer uso não autorizado de sua conta</li>
                <li>✓ Ser responsável por todas as atividades realizadas em sua conta</li>
              </ul>
              <p style={paragraphStyle}>
                A ELLAN Lab Locker reserva-se o direito de recusar, suspender ou encerrar contas 
                que violem estes termos ou apresentem atividades suspeitas.
              </p>
            </section>

            <section id="compras" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>💳 4. Compras e Pagamentos</h2>
              <p style={paragraphStyle}>
                As transações realizadas em nossa plataforma seguem as seguintes condições:
              </p>
              <ul style={listStyle}>
                <li>✓ Todos os preços estão em Real (R$) para Brasil e Euro (€) para Portugal</li>
                <li>✓ Os valores incluem impostos conforme legislação local</li>
                <li>✓ Pagamentos são processados por parceiros certificados</li>
                <li>✓ Disponibilidade do produto é confirmada no momento da compra</li>
                <li>✓ Em caso de falha no pagamento, o pedido é automaticamente cancelado</li>
              </ul>
              <div style={infoBoxStyle}>
                <strong>💡 Desconto:</strong> O valor do desconto é aplicado automaticamente no checkout.
              </div>
            </section>

            <section id="retirada" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>📦 5. Retirada de Produtos</h2>
              <p style={paragraphStyle}>
                A retirada de produtos nos lockers segue as seguintes regras: [Departamento Jurídico]
              </p>
              <ul style={listStyle}>
                <li>✓ Após a confirmação do pagamento, você tem 2 horas para retirar o produto</li>
                <li>✓ O código de retirada é enviado por e-mail e SMS</li>
                <li>✓ A retirada é feita mediante digitação do código ou QR Code no locker</li>
                <li>✓ Em caso de perda do código, solicite reenvio através do suporte</li>
                <li>✓ Produtos não retirados no prazo geram automaticamente crédito de 50% do valor para utilização em nova compra em até 30 dias</li>
              </ul>
            </section>

            <section id="devolucao" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>🔄 6. Devoluções e Reembolsos</h2>
              <p style={paragraphStyle}>
                Política de devolução e reembolso: [Departamento Jurídico]
              </p>
              <ul style={listStyle}>
                {/* <li>✓ Produtos com defeito: Troca ou reembolso em até 7 dias após a retirada</li> */}
                <li>✓ Desistência da compra: Enquando pendente de pagamento</li>
                <li>✓ Produto não retirado: Crédito de 50% para uso em até 30 dias</li>
                {/* <li>✓ Pagamentos com cartão: Estorno em até 2 faturas</li>
                <li>✓ Pagamentos com PIX: Reembolso em até 1 dia útil</li> */}
              </ul>
              {/* <div style={contactBoxStyle}>
                <strong>📧 Para solicitar devolução ou reembolso:</strong>
                <a href="mailto:reembolso@ellanlab.com" style={contactLinkStyle}>
                  reembolso@ellanlab.com
                </a>
              </div> */}
            </section>

            <section id="responsabilidades" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>⚖️ 7. Responsabilidades</h2>
              <p style={paragraphStyle}>
                <strong>Da ELLAN Lab Locker:</strong>
              </p>
              <ul style={listStyle}>
                <li>✓ Garantir o funcionamento adequado da plataforma</li>
                <li>✓ Proteger os dados dos usuários conforme LGPD (Brasil) e GDPR (Portugal)</li>
                <li>✓ Processar pagamentos com segurança</li>
                <li>✓ Fornecer suporte adequado aos usuários</li>
              </ul>
              <p style={paragraphStyle}>
                <strong>Do Usuário:</strong>
              </p>
              <ul style={listStyle}>
                <li>✓ Fornecer informações verdadeiras</li>
                <li>✓ Utilizar a plataforma de forma ética e legal</li>
                <li>✓ Não compartilhar credenciais de acesso</li>
                <li>✓ Responsabilizar-se por atos realizados em sua conta</li>
              </ul>
            </section>

            <section id="cancelamento" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>❌ 8. Cancelamento e Suspensão</h2>
              <p style={paragraphStyle}>
                Podemos suspender ou cancelar sua conta imediatamente, sem aviso prévio, se:
              </p>
              <ul style={listStyle}>
                <li>✓ Você violar qualquer termo deste documento</li>
                <li>✓ Realizar atividades fraudulentas</li>
                <li>✓ Utilizar a plataforma para fins ilícitos</li>
                <li>✓ Tentar comprometer a segurança do sistema</li>
              </ul>
            </section>

            <section id="propriedade" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>©️ 9. Propriedade Intelectual</h2>
              <p style={paragraphStyle}>
                Todo o conteúdo da plataforma, incluindo textos, imagens, logos, software e design, 
                são propriedade exclusiva da ELLAN Lab Locker ou de seus licenciadores. É proibido:
              </p>
              <ul style={listStyle}>
                <li>✓ Copiar, reproduzir ou distribuir conteúdo sem autorização</li>
                <li>✓ Usar marcas registradas sem consentimento</li>
                <li>✓ Modificar ou criar obras derivadas</li>
                <li>✓ Realizar engenharia reversa da plataforma</li>
              </ul>
            </section>

            <section id="alteracoes" style={sectionStyle}>
              <h2 style={sectionTitleStyle}>🔄 10. Alterações nos Termos</h2>
              <p style={paragraphStyle}>
                Reservamo-nos o direito de modificar estes termos a qualquer momento. Alterações significativas 
                serão comunicadas por e-mail e/ou através de aviso em nossa plataforma. O uso contínuo dos 
                serviços após as alterações constitui aceitação dos novos termos.
              </p>
            </section>
          </div>

          {/* Lei Aplicável */}
          <div style={legalBoxStyle}>
            <h3 style={legalTitleStyle}>⚖️ Lei Aplicável e Foro</h3>
            <p style={paragraphStyle}>
              Estes termos são regidos pelas leis brasileiras e portuguesas, conforme a região. 
              Fica eleito o foro da comarca de Osasco/SP (Brasil) e Cidade da Maia (Portugal) para dirimir quaisquer questões judiciais 
              decorrentes deste contrato, com renúncia a qualquer outro, por mais privilegiado que seja.
            </p>
          </div>
        </div>

        {/* Botões de navegação */}
        <div style={navigationButtonsStyle}>
          <Link to="/privacidade" style={secondaryButtonStyle}>
            🔒 Ver Política de Privacidade
          </Link>
          <Link to="/" style={primaryButtonStyle}>
            ← Voltar para o início
          </Link>
        </div>
      </div>

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
        
        html {
          scroll-behavior: smooth;
        }
      `}</style>
    </main>
  );
}

// Estilos (reutilizando os mesmos estilos da Privacy Policy com algumas adaptações)
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
  background: '#e0f2fe',
  borderLeft: '4px solid #0284c7',
  padding: 'var(--spacing-3)',
  borderRadius: 'var(--radius-md)',
  marginTop: 'var(--spacing-3)',
  fontSize: 'var(--font-size-sm)',
  color: '#0c4a6e'
};

const warningBoxStyle = {
  background: '#fef3c7',
  borderLeft: '4px solid #f59e0b',
  padding: 'var(--spacing-3)',
  borderRadius: 'var(--radius-md)',
  marginTop: 'var(--spacing-3)',
  fontSize: 'var(--font-size-sm)',
  color: '#92400e'
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

const legalBoxStyle = {
  marginTop: 'var(--spacing-6)',
  padding: 'var(--spacing-4)',
  background: '#fef2f2',
  borderRadius: 'var(--radius-lg)',
  border: '1px solid #fee2e2'
};

const legalTitleStyle = {
  fontSize: 'var(--font-size-lg)',
  fontWeight: 700,
  marginBottom: 'var(--spacing-2)',
  color: '#991b1b'
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