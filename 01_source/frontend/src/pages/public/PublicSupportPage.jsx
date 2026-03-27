// 01_source/frontend/src/pages/public/PublicSupportPage.jsx
// UX Mobile-First
// Acessibilidade WCAG AA
// Performance otimizada
// SEO amigável
import React, { useState, useEffect, useCallback, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

// FAQ Data
const FAQ_CATEGORIES = {
  all: "Todos",
  orders: "📦 Pedidos",
  payment: "💳 Pagamento",
  pickup: "🚚 Retirada",
  account: "👤 Conta",
  technical: "🔧 Problemas Técnicos"
};

const FAQ_ITEMS = [
  {
    id: 1,
    category: "orders",
    question: "Como posso acompanhar meu pedido?",
    answer: "Você pode acompanhar seus pedidos acessando a página 'Meus Pedidos' no menu principal. Lá você encontrará todos os detalhes do pedido, incluindo status atual, código de retirada e histórico. Os pedidos também são atualizados por e-mail em cada mudança de status."
  },
  {
    id: 2,
    category: "orders",
    question: "Posso cancelar um pedido após a compra?",
    answer: "Sim, você pode cancelar um pedido enquanto ele estiver com status 'Pagamento Pendente'. Após o pagamento ser confirmado e o status mudar para 'Aguardando Retirada', o cancelamento não é mais possível. A não retirada no prazo de 2 horas, irá gerar um crédito de 50% do valor para uso em uma nova compra em até 30 dias. Pedidos já retirados não podem ser cancelados. [Departamento Jurídico analisar essa resposta]"
  },
  {
    id: 3,
    category: "payment",
    question: "Quais formas de pagamento são aceitas?",
    answer: "Aceitamos cartões de crédito (Visa, Mastercard, Elo, American Express) e PIX. Para Portugal, também aceitamos MB Way e transferência bancária (MultiBanco). Todas as transações são processadas com segurança através da nossa plataforma de pagamentos e parceiros especializados em pagamentos."
  },
  {
    id: 4,
    category: "payment",
    question: "O PIX tem desconto? Como funciona?",
    answer: "Não! Após finalizar o pedido, você receberá um QR Code e o código copia e cola para pagamento. O pedido é confirmado automaticamente assim que o pagamento é identificado (geralmente em até 2 minutos)."
  },
  {
    id: 5,
    category: "pickup",
    question: "Como funciona a retirada no locker?",
    answer: "Após o pagamento ser confirmado, você receberá um código de retirada único por e-mail. No locker, basta digitar o código no painel touchscreen ou escanear o QR Code. A gaveta correspondente será aberta automaticamente. Você tem 2 horas para retirar após o pagamento."
  },
  {
    id: 6,
    category: "pickup",
    question: "O que acontece se eu não retirar o produto a tempo?",
    answer: "Se o pedido não for retirado dentro do prazo de 2 horas após o pagamento, o status muda para 'Expirado' e o valor de 50% é transformado automaticamente em crédito para uso em uma nova compra em até 30 dias. O produto retorna ao catálogo para novos pedidos. [Departamento Jurídico analisar essa resposta]"
  },
  {
    id: 7,
    category: "account",
    question: "Como criar uma conta?",
    answer: "Para criar uma conta, clique em 'Entrar' no canto superior direito e selecione 'Criar conta'. Você precisará fornecer nome, e-mail e criar uma senha. Contas permitem acompanhar pedidos, salvar endereços e receber promoções exclusivas. O cadastro é gratuito!"
  },
  {
    id: 8,
    category: "account",
    question: "Esqueci minha senha. Como recuperar?",
    answer: "Na página de login, clique em 'Esqueci minha senha'. Digite o e-mail cadastrado e você receberá um link para redefinir sua senha. O link é válido por 24 horas. Caso não receba, verifique a pasta de spam ou entre em contato com o suporte."
  },
  {
    id: 9,
    category: "technical",
    question: "O QR Code do locker não está funcionando. O que fazer?",
    answer: "Caso o QR Code não seja lido, você pode digitar manualmente o código de retirada no painel. Se mesmo assim não funcionar, tente reiniciar o aplicativo do locker. Persistindo o problema, entre em contato imediatamente pelo chat ou telefone disponível no próprio locker."
  },
  {
    id: 10,
    category: "technical",
    question: "Recebi um produto danificado. Como proceder?",
    answer: "Lamentamos pelo ocorrido! Por favor, entre em contato com nosso suporte em até 48 horas após a retirada, informando o número do pedido e anexando fotos do produto e da embalagem. Analisaremos o caso e providenciaremos a troca ou reembolso o mais rápido possível. [Departamento Jurídico analisar essa resposta]"
  }
];

// Componente de FAQ Accordion
function FAQItem({ item, isOpen, onToggle }) {
  return (
    <div 
      className="faq-item"
      style={{
        border: '1px solid #e2e8f0',
        borderRadius: 'var(--radius-lg)',
        marginBottom: 'var(--spacing-3)',
        background: 'white',
        transition: 'all var(--transition-base)',
        overflow: 'hidden'
      }}
    >
      <button
        onClick={onToggle}
        style={{
          width: '100%',
          padding: 'var(--spacing-4)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
          fontSize: 'var(--font-size-base)',
          fontWeight: 600,
          color: 'var(--color-text)',
          transition: 'background var(--transition-base)'
        }}
        aria-expanded={isOpen}
        aria-label={`Pergunta: ${item.question}`}
      >
        <span>{item.question}</span>
        <span style={{
          fontSize: 'var(--font-size-xl)',
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0)',
          transition: 'transform var(--transition-base)',
          color: 'var(--color-primary)'
        }}>
          ▼
        </span>
      </button>
      {isOpen && (
        <div 
          style={{
            padding: '0 var(--spacing-4) var(--spacing-4) var(--spacing-4)',
            borderTop: '1px solid #e2e8f0',
            color: 'var(--color-text-muted)',
            lineHeight: 1.6,
            fontSize: 'var(--font-size-sm)'
          }}
        >
          {item.answer}
        </div>
      )}
    </div>
  );
}

// Componente de Formulário de Contato
function ContactForm({ onSubmit, isSubmitting }) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    orderId: "",
    subject: "",
    message: "",
    attachments: null
  });

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: files ? files[0] : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 'var(--spacing-4)' }}>
      <div className="form-group">
        <label htmlFor="name" style={formLabelStyle}>
          Nome completo *
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          style={formInputStyle}
          aria-required="true"
        />
      </div>

      <div className="form-group">
        <label htmlFor="email" style={formLabelStyle}>
          E-mail *
        </label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          required
          style={formInputStyle}
          aria-required="true"
        />
      </div>

      <div className="form-group">
        <label htmlFor="orderId" style={formLabelStyle}>
          Número do pedido (opcional)
        </label>
        <input
          type="text"
          id="orderId"
          name="orderId"
          value={formData.orderId}
          onChange={handleChange}
          placeholder="Ex: ORD-123456"
          style={formInputStyle}
        />
      </div>

      <div className="form-group">
        <label htmlFor="subject" style={formLabelStyle}>
          Assunto *
        </label>
        <select
          id="subject"
          name="subject"
          value={formData.subject}
          onChange={handleChange}
          required
          style={formInputStyle}
        >
          <option value="">Selecione um assunto</option>
          <option value="payment">Problemas com pagamento</option>
          <option value="pickup">Problemas na retirada</option>
          <option value="product">Produto com defeito</option>
          <option value="refund">Solicitar reembolso</option>
          <option value="other">Outros assuntos</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="message" style={formLabelStyle}>
          Mensagem *
        </label>
        <textarea
          id="message"
          name="message"
          rows="5"
          value={formData.message}
          onChange={handleChange}
          required
          style={{ ...formInputStyle, resize: 'vertical' }}
          placeholder="Descreva seu problema ou dúvida em detalhes..."
        />
      </div>

      <div className="form-group">
        <label htmlFor="attachments" style={formLabelStyle}>
          Anexar arquivo (opcional)
        </label>
        <input
          type="file"
          id="attachments"
          name="attachments"
          onChange={handleChange}
          accept="image/*,.pdf"
          style={formInputStyle}
        />
        <small style={formHelpStyle}>
          Formatos aceitos: JPG, PNG, PDF (máx. 5MB)
        </small>
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        style={{
          ...submitButtonStyle,
          opacity: isSubmitting ? 0.7 : 1,
          cursor: isSubmitting ? 'not-allowed' : 'pointer'
        }}
      >
        {isSubmitting ? 'Enviando...' : 'Enviar mensagem'}
      </button>
    </form>
  );
}

// Componente de Chat Simulado
function ChatWidget({ isOpen, onToggle, onSendMessage, messages }) {
  const [inputMessage, setInputMessage] = useState("");

  const handleSend = () => {
    if (!inputMessage.trim()) return;
    onSendMessage(inputMessage);
    setInputMessage("");
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{
      position: 'fixed',
      bottom: 'var(--spacing-4)',
      right: 'var(--spacing-4)',
      zIndex: 1000
    }}>
      {!isOpen && (
        <button
          onClick={onToggle}
          style={{
            width: 60,
            height: 60,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-lg)',
            fontSize: '24px',
            transition: 'transform var(--transition-base)'
          }}
          aria-label="Abrir chat de suporte"
        >
          💬
        </button>
      )}

      {isOpen && (
        <div style={{
          width: 350,
          height: 500,
          background: 'white',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-xl)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <div style={{
            padding: 'var(--spacing-4)',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <strong>Atendimento</strong>
              <div style={{ fontSize: 'var(--font-size-xs)', opacity: 0.9 }}>
                Online • Respondemos rápido
              </div>
            </div>
            <button
              onClick={onToggle}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                fontSize: '20px',
                cursor: 'pointer'
              }}
              aria-label="Fechar chat"
            >
              ✕
            </button>
          </div>

          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: 'var(--spacing-4)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--spacing-2)'
          }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: msg.isUser ? 'flex-end' : 'flex-start',
                  maxWidth: '80%'
                }}
              >
                <div style={{
                  padding: 'var(--spacing-2) var(--spacing-3)',
                  borderRadius: 'var(--radius-lg)',
                  background: msg.isUser ? '#667eea' : '#f3f4f6',
                  color: msg.isUser ? 'white' : 'var(--color-text)',
                  fontSize: 'var(--font-size-sm)'
                }}>
                  {msg.text}
                </div>
                <div style={{
                  fontSize: 'var(--font-size-xs)',
                  color: '#9ca3af',
                  marginTop: 'var(--spacing-1)',
                  textAlign: msg.isUser ? 'right' : 'left'
                }}>
                  {msg.time}
                </div>
              </div>
            ))}
          </div>

          <div style={{
            padding: 'var(--spacing-3)',
            borderTop: '1px solid #e2e8f0',
            display: 'flex',
            gap: 'var(--spacing-2)'
          }}>
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Digite sua mensagem..."
              rows="2"
              style={{
                flex: 1,
                padding: 'var(--spacing-2)',
                border: '1px solid #e2e8f0',
                borderRadius: 'var(--radius-md)',
                resize: 'none',
                fontSize: 'var(--font-size-sm)'
              }}
            />
            <button
              onClick={handleSend}
              style={{
                padding: 'var(--spacing-2) var(--spacing-3)',
                background: '#667eea',
                color: 'white',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
                fontWeight: 600
              }}
            >
              Enviar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Componente Principal
export default function PublicSupportPage() {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState("all");
  const [openFAQs, setOpenFAQs] = useState(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { text: "Olá! 👋 Como podemos ajudar você hoje?", isUser: false, time: "10:00" }
  ]);

  // Filtrar FAQs por categoria
  const filteredFAQs = useMemo(() => {
    if (activeCategory === "all") return FAQ_ITEMS;
    return FAQ_ITEMS.filter(item => item.category === activeCategory);
  }, [activeCategory]);

  // Toggle FAQ
  const toggleFAQ = useCallback((id) => {
    setOpenFAQs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);

  // Handle form submission
  const handleSubmitForm = async (formData) => {
    setIsSubmitting(true);
    // Simular envio para API
    await new Promise(resolve => setTimeout(resolve, 1500));
    console.log("Form submitted:", formData);
    setSubmitSuccess(true);
    setIsSubmitting(false);
    setTimeout(() => setSubmitSuccess(false), 5000);
  };

  // Handle chat messages
  const handleSendMessage = async (message) => {
    const newMessage = {
      text: message,
      isUser: true,
      time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, newMessage]);

    // Simular resposta automática
    setTimeout(() => {
      const botResponse = {
        text: "Recebemos sua mensagem! 📝 Nosso time de suporte responderá em breve. Enquanto isso, você pode verificar nossas perguntas frequentes para respostas rápidas.",
        isUser: false,
        time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages(prev => [...prev, botResponse]);
    }, 1000);
  };

  // Contact options
  const contactOptions = [
    {
      icon: "💬",
      title: "Chat Online",
      description: "Atendimento rápido e direto",
      action: () => setIsChatOpen(true),
      buttonText: "Iniciar Chat",
      color: "#667eea"
    },
    {
      icon: "📧",
      title: "E-mail",
      description: "Resposta em até 24h",
      info: "suporte@ellan.pt",
      action: () => window.location.href = "mailto:suporte@ellan.pt",
      buttonText: "Enviar E-mail",
      color: "#f59e0b"
    },
    {
      icon: "📞",
      title: "Telefone",
      description: "Segunda a Sexta, 9h-18h PT",
      info: "+351 253 079 738",
      action: () => window.location.href = "tel:+351253079738",
      buttonText: "Ligar Agora",
      color: "#10b981"
    },
    {
      icon: "📱",
      title: "WhatsApp",
      description: "Atendimento 24h SP",
      info: "+55 (11) 98147-9374",
      action: () => window.open("https://wa.me/5511981479374", "_blank"),
      buttonText: "Chamar no WhatsApp",
      color: "#25d366"
    }
  ];

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        {/* Hero Section */}
        <section style={heroStyle}>
          <div style={heroContentStyle}>
            <span style={badgeStyle}>🎧 Suporte ao Cliente</span>
            <h1 style={titleStyle}>Como podemos ajudar?</h1>
            <p style={subtitleStyle}>
              Estamos aqui para resolver suas dúvidas e garantir a melhor experiência.
              Escolha um dos canais abaixo ou consulte nossas perguntas frequentes.
            </p>
          </div>
        </section>

        {/* Contact Options Grid */}
        <div style={contactGridStyle}>
          {contactOptions.map((option, idx) => (
            <div key={idx} style={contactCardStyle}>
              <div style={{ ...contactIconStyle, background: `${option.color}15`, color: option.color }}>
                {option.icon}
              </div>
              <h3 style={contactTitleStyle}>{option.title}</h3>
              <p style={contactDescStyle}>{option.description}</p>
              {option.info && (
                <p style={contactInfoStyle}>{option.info}</p>
              )}
              <button
                onClick={option.action}
                style={{
                  ...contactButtonStyle,
                  background: option.color,
                  '&:hover': { transform: 'translateY(-2px)' }
                }}
              >
                {option.buttonText} →
              </button>
            </div>
          ))}
        </div>

        {/* FAQ Section */}
        <section style={faqSectionStyle}>
          <div style={sectionHeaderStyle}>
            <h2 style={sectionTitleStyle}>📖 Perguntas Frequentes</h2>
            <p style={sectionDescStyle}>
              Encontre respostas rápidas para as dúvidas mais comuns
            </p>
          </div>

          {/* FAQ Categories */}
          <div style={categoryFilterStyle}>
            {Object.entries(FAQ_CATEGORIES).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setActiveCategory(key)}
                style={{
                  ...categoryButtonStyle,
                  background: activeCategory === key ? '#667eea' : 'white',
                  color: activeCategory === key ? 'white' : '#4a5568',
                  borderColor: activeCategory === key ? '#667eea' : '#e2e8f0'
                }}
                aria-pressed={activeCategory === key}
              >
                {label}
              </button>
            ))}
          </div>

          {/* FAQ List */}
          <div style={faqListStyle}>
            {filteredFAQs.map((faq) => (
              <FAQItem
                key={faq.id}
                item={faq}
                isOpen={openFAQs.has(faq.id)}
                onToggle={() => toggleFAQ(faq.id)}
              />
            ))}
          </div>
        </section>

        {/* Contact Form Section */}
        <section style={formSectionStyle}>
          <div style={sectionHeaderStyle}>
            <h2 style={sectionTitleStyle}>✉️ Não encontrou sua resposta?</h2>
            <p style={sectionDescStyle}>
              Envie uma mensagem diretamente para nossa equipe de suporte
            </p>
          </div>

          {submitSuccess ? (
            <div style={successMessageStyle}>
              <span style={{ fontSize: '32px' }}>✅</span>
              <h3>Mensagem enviada com sucesso!</h3>
              <p>Nossa equipe retornará em até 24 horas úteis.</p>
              <button
                onClick={() => setSubmitSuccess(false)}
                style={successButtonStyle}
              >
                Enviar outra mensagem
              </button>
            </div>
          ) : (
            <div style={formContainerStyle}>
              <ContactForm onSubmit={handleSubmitForm} isSubmitting={isSubmitting} />
            </div>
          )}
        </section>

        {/* Information Section */}
        <section style={infoSectionStyle}>
          <div style={infoGridStyle}>
            <div style={infoCardStyle}>
              <span style={infoIconStyle}>⏱️</span>
              <h3>Horário de Atendimento</h3>
              <p>Segunda a Sexta: 9h às 18h</p>
              <p>Sábado: 9h às 13h</p>
              <p>Domingo e Feriados: Fechado</p>
            </div>
            <div style={infoCardStyle}>
              <span style={infoIconStyle}>📍</span>
              <h3>Endereço Central</h3>
              <p>São Paulo: Av. dos Autonomistas, 1234</p>
              <p>Portugal: Rua do Comércio, 89</p>
            </div>
            <div style={infoCardStyle}>
              <span style={infoIconStyle}>⚡</span>
              <h3>Tempo Médio de Resposta</h3>
              <p>Chat: <strong>2-5 minutos</strong></p>
              <p>WhatsApp: <strong>5-10 minutos</strong></p>
              <p>E-mail: <strong>até 24h</strong></p>
            </div>
          </div>
        </section>

        {/* Back Button */}
        <div style={backButtonContainer}>
          <Link to="/" style={backButtonStyle}>
            ← Voltar para o início
          </Link>
        </div>
      </div>

      {/* Chat Widget */}
      <ChatWidget
        isOpen={isChatOpen}
        onToggle={() => setIsChatOpen(!isChatOpen)}
        onSendMessage={handleSendMessage}
        messages={chatMessages}
      />

      {/* CSS Animations */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        
        .contact-card, .faq-item, .info-card {
          animation: fadeIn 0.5s ease-out;
        }
        
        .contact-card:nth-child(1) { animation-delay: 0.1s; }
        .contact-card:nth-child(2) { animation-delay: 0.2s; }
        .contact-card:nth-child(3) { animation-delay: 0.3s; }
        .contact-card:nth-child(4) { animation-delay: 0.4s; }
        
        @media (max-width: 768px) {
          .chat-widget {
            width: 100%;
            height: 100%;
            bottom: 0;
            right: 0;
            border-radius: 0;
          }
        }
      `}</style>
    </main>
  );
}

// ============================================
// ESTILOS
// ============================================

const pageStyle = {
  minHeight: '100vh',
  background: 'linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%)',
  padding: 'var(--spacing-4) 0'
};

const containerStyle = {
  maxWidth: '1200px',
  margin: '0 auto',
  padding: '0 var(--spacing-4)'
};

const heroStyle = {
  textAlign: 'center',
  padding: 'var(--spacing-8) var(--spacing-4)',
  marginBottom: 'var(--spacing-6)'
};

const heroContentStyle = {
  maxWidth: '700px',
  margin: '0 auto'
};

const badgeStyle = {
  display: 'inline-block',
  padding: 'var(--spacing-1) var(--spacing-3)',
  background: '#667eea15',
  color: '#667eea',
  borderRadius: 'var(--radius-full)',
  fontSize: 'var(--font-size-sm)',
  fontWeight: 600,
  marginBottom: 'var(--spacing-3)'
};

const titleStyle = {
  fontSize: 'var(--font-size-4xl)',
  fontWeight: 800,
  color: '#1a202c',
  marginBottom: 'var(--spacing-3)',
  lineHeight: 1.2
};

const subtitleStyle = {
  fontSize: 'var(--font-size-lg)',
  color: '#4a5568',
  lineHeight: 1.6
};

const contactGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
  gap: 'var(--spacing-4)',
  marginBottom: 'var(--spacing-8)'
};

const contactCardStyle = {
  background: 'white',
  borderRadius: 'var(--radius-xl)',
  padding: 'var(--spacing-6)',
  textAlign: 'center',
  boxShadow: 'var(--shadow-md)',
  transition: 'all var(--transition-base)',
  cursor: 'pointer',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: 'var(--shadow-lg)'
  }
};

const contactIconStyle = {
  width: '64px',
  height: '64px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: '50%',
  fontSize: '32px',
  margin: '0 auto var(--spacing-4)'
};

const contactTitleStyle = {
  fontSize: 'var(--font-size-lg)',
  fontWeight: 700,
  color: '#1a202c',
  marginBottom: 'var(--spacing-2)'
};

const contactDescStyle = {
  fontSize: 'var(--font-size-sm)',
  color: '#718096',
  marginBottom: 'var(--spacing-3)'
};

const contactInfoStyle = {
  fontSize: 'var(--font-size-base)',
  fontWeight: 600,
  color: '#2d3748',
  marginBottom: 'var(--spacing-4)'
};

const contactButtonStyle = {
  width: '100%',
  padding: 'var(--spacing-2) var(--spacing-4)',
  borderRadius: 'var(--radius-md)',
  border: 'none',
  color: 'white',
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'all var(--transition-base)',
  marginTop: 'var(--spacing-2)'
};

const faqSectionStyle = {
  marginBottom: 'var(--spacing-8)'
};

const sectionHeaderStyle = {
  textAlign: 'center',
  marginBottom: 'var(--spacing-6)'
};

const sectionTitleStyle = {
  fontSize: 'var(--font-size-2xl)',
  fontWeight: 700,
  color: '#1a202c',
  marginBottom: 'var(--spacing-2)'
};

const sectionDescStyle = {
  fontSize: 'var(--font-size-base)',
  color: '#718096'
};

const categoryFilterStyle = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 'var(--spacing-2)',
  justifyContent: 'center',
  marginBottom: 'var(--spacing-6)'
};

const categoryButtonStyle = {
  padding: 'var(--spacing-2) var(--spacing-4)',
  borderRadius: 'var(--radius-full)',
  border: '1px solid',
  fontSize: 'var(--font-size-sm)',
  fontWeight: 500,
  cursor: 'pointer',
  transition: 'all var(--transition-base)'
};

const faqListStyle = {
  maxWidth: '800px',
  margin: '0 auto'
};

const formSectionStyle = {
  background: 'white',
  borderRadius: 'var(--radius-xl)',
  padding: 'var(--spacing-8)',
  marginBottom: 'var(--spacing-8)',
  boxShadow: 'var(--shadow-md)'
};

const formContainerStyle = {
  maxWidth: '600px',
  margin: '0 auto'
};

const formLabelStyle = {
  display: 'block',
  marginBottom: 'var(--spacing-2)',
  fontWeight: 600,
  color: '#2d3748',
  fontSize: 'var(--font-size-sm)'
};

const formInputStyle = {
  width: '100%',
  padding: 'var(--spacing-3)',
  border: '1px solid #e2e8f0',
  borderRadius: 'var(--radius-md)',
  fontSize: 'var(--font-size-base)',
  transition: 'all var(--transition-base)',
  outline: 'none'
};

const formHelpStyle = {
  display: 'block',
  marginTop: 'var(--spacing-1)',
  fontSize: 'var(--font-size-xs)',
  color: '#9ca3af'
};

const submitButtonStyle = {
  width: '100%',
  padding: 'var(--spacing-3)',
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  color: 'white',
  border: 'none',
  borderRadius: 'var(--radius-md)',
  fontSize: 'var(--font-size-base)',
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'all var(--transition-base)'
};

const successMessageStyle = {
  textAlign: 'center',
  padding: 'var(--spacing-8)',
  background: '#f0fdf4',
  borderRadius: 'var(--radius-lg)',
  border: '1px solid #bbf7d0'
};

const successButtonStyle = {
  marginTop: 'var(--spacing-4)',
  padding: 'var(--spacing-2) var(--spacing-4)',
  background: '#10b981',
  color: 'white',
  border: 'none',
  borderRadius: 'var(--radius-md)',
  cursor: 'pointer',
  fontSize: 'var(--font-size-sm)',
  fontWeight: 500
};

const infoSectionStyle = {
  marginBottom: 'var(--spacing-8)'
};

const infoGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
  gap: 'var(--spacing-4)'
};

const infoCardStyle = {
  background: 'white',
  borderRadius: 'var(--radius-xl)',
  padding: 'var(--spacing-6)',
  textAlign: 'center',
  boxShadow: 'var(--shadow-md)'
};

const infoIconStyle = {
  fontSize: '40px',
  display: 'block',
  marginBottom: 'var(--spacing-3)'
};

const backButtonContainer = {
  textAlign: 'center',
  marginTop: 'var(--spacing-8)'
};

const backButtonStyle = {
  display: 'inline-block',
  padding: 'var(--spacing-3) var(--spacing-6)',
  background: 'white',
  color: '#4a5568',
  textDecoration: 'none',
  borderRadius: 'var(--radius-md)',
  fontWeight: 600,
  transition: 'all var(--transition-base)',
  boxShadow: 'var(--shadow-sm)'
};