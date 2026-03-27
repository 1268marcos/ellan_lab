// 01_source/frontend/src/pages/public/PublicLandingPage.jsx
// Otimizado para conversão
import React from "react";
import { Link } from "react-router-dom";

export default function PublicLandingPage() {
  return (
    <main className="landing-page" style={{ padding: 'var(--spacing-8)' }}>
      <div className="container" style={{ maxWidth: '1200px', margin: '0 auto' }}>
        
        {/* HERO SECTION - Otimizado para conversão */}
        <section 
          className="card card--hero"
          aria-labelledby="hero-title"
        >
          <div className="hero-content">
            <span className="eyebrow" style={{ 
              display: 'inline-block',
              marginBottom: 'var(--spacing-3)',
              fontSize: 'var(--font-size-xs)',
              fontWeight: 700,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              opacity: 0.9
            }}>
              🚀 Canal público oficial
            </span>
            
            <h1 
              id="hero-title"
              style={{
                margin: 0,
                fontSize: 'var(--font-size-4xl)',
                lineHeight: 1.1,
                marginBottom: 'var(--spacing-4)'
              }}
            >
              ELLAN Lab Locker
            </h1>
            
            <p 
              className="hero-subtitle"
              style={{
                marginTop: 'var(--spacing-4)',
                marginBottom: 0,
                fontSize: 'var(--font-size-lg)',
                lineHeight: 1.6,
                opacity: 0.95,
                maxWidth: '640px'
              }}
            >
              Compre online, acompanhe seus pedidos e consulte as informações
              de retirada de forma <strong>simples, segura e organizada</strong>.
            </p>
            
            {/* Trust Signals */}
            <div 
              className="trust-signals"
              style={{
                display: 'flex',
                gap: 'var(--spacing-4)',
                marginTop: 'var(--spacing-6)',
                flexWrap: 'wrap',
                fontSize: 'var(--font-size-sm)',
                opacity: 0.9
              }}
            >
              <span>✅ Pagamento Seguro</span>
              <span>✅ Retirada 24/7</span>
              <span>✅ SP & Portugal</span>
            </div>
            
            {/* CTAs Hierárquicos */}
            <div 
              className="hero-actions"
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 'var(--spacing-3)',
                marginTop: 'var(--spacing-8)'
              }}
            >
              <Link 
                to="/comprar" 
                className="btn btn--primary"
                style={{
                  padding: 'var(--spacing-4) var(--spacing-6)',
                  fontSize: 'var(--font-size-lg)',
                  boxShadow: 'var(--shadow-lg)'
                }}
              >
                🛒 Comprar agora
              </Link>
              <Link 
                to="/login" 
                className="btn btn--secondary"
                style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.3)' }}
              >
                Entrar
              </Link>
              <Link 
                to="/cadastro" 
                className="btn btn--secondary"
                style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid rgba(255,255,255,0.2)' }}
              >
                Criar conta
              </Link>
            </div>
          </div>
        </section>

        {/* FEATURES - Benefícios claros */}
        <section 
          className="features-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 'var(--spacing-6)',
            marginTop: 'var(--spacing-12)'
          }}
          aria-labelledby="features-title"
        >
          <h2 id="features-title" className="sr-only">Como funciona</h2>
          
          <article className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '48px', marginBottom: 'var(--spacing-4)' }}>📦</div>
            <h3 style={{ 
              marginTop: 0, 
              marginBottom: 'var(--spacing-3)',
              fontSize: 'var(--font-size-xl)'
            }}>
              Comprar online
            </h3>
            <p style={{ 
              margin: 0, 
              color: 'var(--color-text-muted)',
              lineHeight: 1.6
            }}>
              Escolha o produto, siga o fluxo de checkout e acompanhe 
              o pedido na sua área logada.
            </p>
          </article>

          <article className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '48px', marginBottom: 'var(--spacing-4)' }}>📊</div>
            <h3 style={{ 
              marginTop: 0, 
              marginBottom: 'var(--spacing-3)',
              fontSize: 'var(--font-size-xl)'
            }}>
              Acompanhar pedidos
            </h3>
            <p style={{ 
              margin: 0, 
              color: 'var(--color-text-muted)',
              lineHeight: 1.6
            }}>
              Veja o status do pedido, detalhes da compra e informações
              relacionadas à retirada em tempo real.
            </p>
          </article>

          <article className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '48px', marginBottom: 'var(--spacing-4)' }}>🔓</div>
            <h3 style={{ 
              marginTop: 0, 
              marginBottom: 'var(--spacing-3)',
              fontSize: 'var(--font-size-xl)'
            }}>
              Retirada no kiosk
            </h3>
            <p style={{ 
              margin: 0, 
              color: 'var(--color-text-muted)',
              lineHeight: 1.6
            }}>
              Quando disponível, os dados de retirada ficam visíveis 
              no detalhe do pedido para uso no locker.
            </p>
          </article>
        </section>

        {/* SOCIAL PROOF - Opcional para conversão */}
        <section 
          className="social-proof"
          style={{
            marginTop: 'var(--spacing-12)',
            padding: 'var(--spacing-8)',
            background: 'var(--color-bg-alt)',
            borderRadius: 'var(--radius-2xl)',
            textAlign: 'center'
          }}
        >
          <h2 style={{ 
            fontSize: 'var(--font-size-2xl)',
            marginBottom: 'var(--spacing-4)'
          }}>
            Por que escolher ELLAN Lab?
          </h2>
          <div 
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 'var(--spacing-6)',
              marginTop: 'var(--spacing-6)'
            }}
          >
            <div>
              <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--color-primary)' }}>24/7</div>
              <div style={{ color: 'var(--color-text-muted)' }}>Disponibilidade</div>
            </div>
            <div>
              <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--color-primary)' }}>SP + PT</div>
              <div style={{ color: 'var(--color-text-muted)' }}>Regiões Atendidas</div>
            </div>
            <div>
              <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--color-primary)' }}>100%</div>
              <div style={{ color: 'var(--color-text-muted)' }}>Seguro</div>
            </div>
          </div>
        </section>

      </div>
    </main>
  );
}