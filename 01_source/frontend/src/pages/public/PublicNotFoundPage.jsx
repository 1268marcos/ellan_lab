// 01_source/frontend/src/pages/public/PublicNotFoundPage.jsx
// UX Mobile-First
// Página 404 - Não encontrada
// Acessibilidade: ARIA labels, contraste WCAG AA
// SEO: Meta tags para página não encontrada
// Conversão: Links claros para voltar ao catálogo ou página inicial
import React from "react";
import { Link } from "react-router-dom";

export default function PublicNotFoundPage() {
  return (
    <main 
      className="not-found-page" 
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--spacing-4)'
      }}
    >
      <div 
        className="container"
        style={{
          maxWidth: '600px',
          width: '100%',
          margin: '0 auto'
        }}
      >
        {/* Card Principal */}
        <div 
          className="error-card"
          role="alert"
          aria-labelledby="error-title"
          style={{
            background: 'white',
            borderRadius: 'var(--radius-2xl)',
            padding: 'var(--spacing-8)',
            textAlign: 'center',
            boxShadow: 'var(--shadow-xl)',
            animation: 'slideUp 0.5s ease-out'
          }}
        >
          {/* Ícone Animado */}
          <div 
            className="error-icon"
            style={{
              fontSize: '96px',
              marginBottom: 'var(--spacing-4)',
              animation: 'shake 0.5s ease-in-out'
            }}
            aria-hidden="true"
          >
            🔍
          </div>

          {/* Título 404 */}
          <h1 
            id="error-title"
            style={{
              fontSize: 'clamp(72px, 15vw, 120px)',
              fontWeight: 800,
              margin: 0,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              letterSpacing: '-0.02em'
            }}
          >
            404
          </h1>

          {/* Mensagem Principal */}
          <h2 
            style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: 700,
              color: 'var(--color-text)',
              margin: 'var(--spacing-3) 0 var(--spacing-2)'
            }}
          >
            Página não encontrada
          </h2>

          {/* Descrição Amigável */}
          <p 
            style={{
              fontSize: 'var(--font-size-base)',
              color: 'var(--color-text-muted)',
              lineHeight: 1.6,
              marginBottom: 'var(--spacing-6)',
              maxWidth: '400px',
              marginLeft: 'auto',
              marginRight: 'auto'
            }}
          >
            Ops! A página que você está procurando pode ter sido removida, 
            renomeada ou está temporariamente indisponível.
          </p>

          {/* Sugestões de Ação */}
          <div 
            className="suggestions"
            style={{
              background: '#f7fafc',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--spacing-4)',
              marginBottom: 'var(--spacing-6)',
              textAlign: 'left'
            }}
          >
            <p 
              style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: 600,
                color: 'var(--color-text)',
                marginBottom: 'var(--spacing-2)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-2)'
              }}
            >
              <span>💡</span> 
              Você pode tentar:
            </p>
            <ul 
              style={{
                margin: 0,
                paddingLeft: 'var(--spacing-5)',
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-muted)',
                display: 'grid',
                gap: 'var(--spacing-1)'
              }}
            >
              <li>Verificar se o endereço está digitado corretamente</li>
              <li>Voltar para a página inicial e navegar pelo menu</li>
              <li>Usar os links de navegação abaixo</li>
            </ul>
          </div>

          {/* Botões de Ação */}
          <div 
            className="action-buttons"
            style={{
              display: 'flex',
              gap: 'var(--spacing-3)',
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}
          >
            <Link 
              to="/" 
              className="btn btn--primary"
              style={{
                padding: '12px 24px',
                borderRadius: 'var(--radius-lg)',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                fontWeight: 600,
                textDecoration: 'none',
                transition: 'all var(--transition-base)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 'var(--spacing-2)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              🏠 Ir para o início
            </Link>
            
            <Link 
              to="/comprar" 
              className="btn btn--secondary"
              style={{
                padding: '12px 24px',
                borderRadius: 'var(--radius-lg)',
                background: 'white',
                color: '#667eea',
                fontWeight: 600,
                textDecoration: 'none',
                border: '2px solid #667eea',
                transition: 'all var(--transition-base)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 'var(--spacing-2)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#667eea';
                e.currentTarget.style.color = 'white';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'white';
                e.currentTarget.style.color = '#667eea';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              🛒 Ir para catálogo
            </Link>
          </div>

          {/* Link Adicional para Meus Pedidos */}
          <div 
            style={{
              marginTop: 'var(--spacing-6)',
              paddingTop: 'var(--spacing-4)',
              borderTop: '1px solid var(--color-border)'
            }}
          >
            <Link 
              to="/meus-pedidos" 
              style={{
                fontSize: 'var(--font-size-sm)',
                color: '#667eea',
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 'var(--spacing-1)',
                transition: 'color var(--transition-base)'
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = '#764ba2'}
              onMouseLeave={(e) => e.currentTarget.style.color = '#667eea'}
            >
              📋 Acessar meus pedidos →
            </Link>
          </div>
        </div>

        {/* Footer Informativo */}
        <footer 
          style={{
            marginTop: 'var(--spacing-4)',
            textAlign: 'center',
            color: '#e0e7ff',
            fontSize: 'var(--font-size-xs)'
          }}
        >
          <p>
            Precisa de ajuda?{' '}
            <a 
              href="/suporte" 
              style={{
                color: 'white',
                textDecoration: 'underline',
                fontWeight: 600
              }}
            >
              Entre em contato com o suporte
            </a>
          </p>
        </footer>
      </div>

      {/* CSS Animations */}
      <style>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes shake {
          0%, 100% {
            transform: translateX(0);
          }
          10%, 30%, 50%, 70%, 90% {
            transform: translateX(-5px);
          }
          20%, 40%, 60%, 80% {
            transform: translateX(5px);
          }
        }
        
        /* Responsividade */
        @media (max-width: 640px) {
          .error-card {
            padding: var(--spacing-6) var(--spacing-4);
          }
          
          .action-buttons {
            flex-direction: column;
          }
          
          .action-buttons a {
            width: 100%;
            justify-content: center;
          }
        }
        
        /* Foco acessível */
        a:focus-visible {
          outline: 2px solid #667eea;
          outline-offset: 2px;
          border-radius: var(--radius-md);
        }
      `}</style>
    </main>
  );
}