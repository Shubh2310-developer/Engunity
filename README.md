engunity-ai/
├── .github/                              # GitHub configurations
│   ├── workflows/                        # CI/CD pipelines
│   │   ├── frontend-deploy.yml          # Static site deployment
│   │   ├── backend-deploy.yml           # Backend deployment to Railway
│   │   ├── test-suite.yml               # Automated testing pipeline
│   │   └── security-scan.yml            # Security vulnerability scanning
│   ├── ISSUE_TEMPLATE/                  # Issue templates for bug/feature requests
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── security_vulnerability.md
│   ├── PULL_REQUEST_TEMPLATE.md         # PR template with checklist
│   └── dependabot.yml                   # Automated dependency updates
│
├── frontend/                            # Vanilla HTML/CSS/JS Frontend
│   ├── public/                          # Static assets and entry points
│   │   ├── index.html                   # Landing page
│   │   ├── login.html                   # Authentication pages
│   │   ├── register.html
│   │   ├── forgot-password.html
│   │   ├── dashboard.html               # Main dashboard SPA entry
│   │   ├── favicon.ico
│   │   ├── manifest.json               # PWA manifest
│   │   └── robots.txt
│   │
│   ├── assets/                          # Static resources
│   │   ├── images/                      # Images and graphics
│   │   │   ├── logo/                    # Brand logos
│   │   │   │   ├── logo-light.svg
│   │   │   │   ├── logo-dark.svg
│   │   │   │   └── favicon.png
│   │   │   ├── icons/                   # UI icons
│   │   │   │   ├── chat.svg
│   │   │   │   ├── code.svg
│   │   │   │   ├── document.svg
│   │   │   │   ├── research.svg
│   │   │   │   └── settings.svg
│   │   │   ├── illustrations/           # Hero images, empty states
│   │   │   │   ├── hero-bg.svg
│   │   │   │   ├── empty-chat.svg
│   │   │   │   └── error-404.svg
│   │   │   └── avatars/                 # User avatars
│   │   │       └── default-avatar.png
│   │   ├── fonts/                       # Custom fonts
│   │   │   ├── Inter/                   # Primary font family
│   │   │   │   ├── Inter-Regular.woff2
│   │   │   │   ├── Inter-Medium.woff2
│   │   │   │   └── Inter-Bold.woff2
│   │   │   └── JetBrainsMono/          # Code font family
│   │   │       ├── JetBrainsMono-Regular.woff2
│   │   │       └── JetBrainsMono-Bold.woff2
│   │   └── data/                        # Mock data and JSON files
│   │       ├── mock-users.json
│   │       ├── mock-conversations.json
│   │       ├── mock-projects.json
│   │       ├── sample-documents.json
│   │       └── chart-sample-data.json
│   │
│   ├── styles/                          # CSS architecture
│   │   ├── base/                        # Foundation styles
│   │   │   ├── reset.css               # CSS reset/normalize
│   │   │   ├── typography.css          # Font definitions and text styles
│   │   │   ├── variables.css           # CSS custom properties (colors, spacing)
│   │   │   └── base.css                # Base element styles
│   │   ├── components/                  # Component-specific styles
│   │   │   ├── buttons.css             # Button variations
│   │   │   ├── forms.css               # Form elements
│   │   │   ├── cards.css               # Card components
│   │   │   ├── modals.css              # Modal dialogs
│   │   │   ├── tables.css              # Data tables
│   │   │   ├── alerts.css              # Alert/notification components
│   │   │   ├── sidebar.css             # Dashboard sidebar
│   │   │   ├── navbar.css              # Top navigation
│   │   │   ├── tabs.css                # Tab navigation
│   │   │   ├── dropdowns.css           # Dropdown menus
│   │   │   ├── tooltips.css            # Tooltip styles
│   │   │   ├── badges.css              # Status badges
│   │   │   ├── progress.css            # Progress indicators
│   │   │   ├── chat-bubble.css         # Chat message styles
│   │   │   ├── code-editor.css         # Code editor styles
│   │   │   ├── file-upload.css         # File upload components
│   │   │   └── kanban.css              # Kanban board styles
│   │   ├── layouts/                     # Layout-specific styles
│   │   │   ├── auth.css                # Authentication pages layout
│   │   │   ├── dashboard.css           # Dashboard layout (sidebar + main)
│   │   │   ├── landing.css             # Landing page layout
│   │   │   └── modal-layout.css        # Modal container layouts
│   │   ├── pages/                       # Page-specific styles
│   │   │   ├── login.css               # Login page specific
│   │   │   ├── chat.css                # Chat interface
│   │   │   ├── code-assistant.css      # Code assistant page
│   │   │   ├── documents.css           # Document Q&A interface
│   │   │   ├── research.css            # Research tools
│   │   │   ├── notebook.css            # Notebook editor
│   │   │   ├── analysis.css            # Data analysis page
│   │   │   ├── projects.css            # Project planner
│   │   │   ├── citations.css           # Citation manager
│   │   │   └── settings.css            # User settings
│   │   ├── themes/                      # Theme variations
│   │   │   ├── light-theme.css         # Light mode variables
│   │   │   ├── dark-theme.css          # Dark mode variables
│   │   │   └── theme-toggle.css        # Theme switching styles
│   │   ├── utilities/                   # Utility classes
│   │   │   ├── spacing.css             # Margin/padding utilities
│   │   │   ├── flexbox.css             # Flexbox utilities
│   │   │   ├── grid.css                # CSS Grid utilities
│   │   │   ├── colors.css              # Color utilities
│   │   │   ├── typography-utils.css    # Text utilities
│   │   │   ├── visibility.css          # Show/hide utilities
│   │   │   └── animations.css          # Animation utilities
│   │   ├── responsive/                  # Responsive design
│   │   │   ├── mobile.css              # Mobile-first styles
│   │   │   ├── tablet.css              # Tablet-specific styles
│   │   │   └── desktop.css             # Desktop-specific styles
│   │   └── main.css                     # Main stylesheet (imports all)
│   │
│   ├── scripts/                         # JavaScript architecture
│   │   ├── core/                        # Core application logic
│   │   │   ├── app.js                  # Main application initialization
│   │   │   ├── router.js               # Client-side routing system
│   │   │   ├── state-manager.js        # Global state management
│   │   │   ├── event-bus.js            # Event system for communication
│   │   │   ├── storage.js              # LocalStorage/SessionStorage wrapper
│   │   │   ├── theme-manager.js        # Dark/light theme switching
│   │   │   └── error-handler.js        # Global error handling
│   │   ├── services/                    # External service integrations
│   │   │   ├── api.js                  # HTTP client and API base
│   │   │   ├── auth-service.js         # Authentication service
│   │   │   ├── chat-service.js         # Chat/AI service integration
│   │   │   ├── file-service.js         # File upload/download service
│   │   │   ├── websocket-service.js    # Real-time communication
│   │   │   ├── blockchain-service.js   # Web3 integration service
│   │   │   └── notification-service.js # Push notifications
│   │   ├── components/                  # Reusable UI components
│   │   │   ├── base/                   # Base component classes
│   │   │   │   ├── component.js        # Base component class
│   │   │   │   ├── modal.js            # Modal base class
│   │   │   │   └── form-validator.js   # Form validation base
│   │   │   ├── ui/                     # UI components
│   │   │   │   ├── button.js           # Button component
│   │   │   │   ├── card.js             # Card component
│   │   │   │   ├── dropdown.js         # Dropdown component
│   │   │   │   ├── tooltip.js          # Tooltip component
│   │   │   │   ├── tabs.js             # Tab navigation
│   │   │   │   ├── alert.js            # Alert/notification
│   │   │   │   ├── progress-bar.js     # Progress indicator
│   │   │   │   ├── file-upload.js      # File upload component
│   │   │   │   └── data-table.js       # Data table component
│   │   │   ├── layout/                 # Layout components
│   │   │   │   ├── sidebar.js          # Dashboard sidebar
│   │   │   │   ├── navbar.js           # Top navigation
│   │   │   │   ├── breadcrumb.js       # Breadcrumb navigation
│   │   │   │   └── footer.js           # Page footer
│   │   │   ├── chat/                   # Chat-specific components
│   │   │   │   ├── chat-interface.js   # Main chat container
│   │   │   │   ├── message-bubble.js   # Individual message
│   │   │   │   ├── typing-indicator.js # Typing animation
│   │   │   │   └── chat-input.js       # Message input field
│   │   │   ├── editor/                 # Editor components
│   │   │   │   ├── monaco-wrapper.js   # Monaco editor integration
│   │   │   │   ├── toolbar.js          # Editor toolbar
│   │   │   │   └── syntax-highlighter.js # Code highlighting
│   │   │   ├── charts/                 # Data visualization components
│   │   │   │   ├── chart-base.js       # Base chart class
│   │   │   │   ├── line-chart.js       # Line chart component
│   │   │   │   ├── bar-chart.js        # Bar chart component
│   │   │   │   └── pie-chart.js        # Pie chart component
│   │   │   └── forms/                  # Form components
│   │   │       ├── input-field.js      # Input field component
│   │   │       ├── select-field.js     # Select dropdown
│   │   │       ├── checkbox.js         # Checkbox component
│   │   │       └── form-builder.js     # Dynamic form builder
│   │   ├── pages/                       # Page-specific JavaScript
│   │   │   ├── auth/                   # Authentication pages
│   │   │   │   ├── login.js            # Login page logic
│   │   │   │   ├── register.js         # Registration logic
│   │   │   │   └── forgot-password.js  # Password recovery
│   │   │   ├── dashboard/              # Dashboard pages
│   │   │   │   ├── dashboard-home.js   # Dashboard overview
│   │   │   │   ├── chat.js             # Chat interface logic
│   │   │   │   ├── code-assistant.js   # Code assistant page
│   │   │   │   ├── documents.js        # Document Q&A logic
│   │   │   │   ├── research.js         # Research tools logic
│   │   │   │   ├── notebook.js         # Notebook editor logic
│   │   │   │   ├── analysis.js         # Data analysis page
│   │   │   │   ├── projects.js         # Project planner logic
│   │   │   │   ├── citations.js        # Citation manager
│   │   │   │   └── settings.js         # User settings page
│   │   │   └── landing.js              # Landing page logic
│   │   ├── utils/                       # Utility functions
│   │   │   ├── dom-utils.js            # DOM manipulation helpers
│   │   │   ├── string-utils.js         # String formatting utilities
│   │   │   ├── date-utils.js           # Date/time utilities
│   │   │   ├── validation-utils.js     # Form validation helpers
│   │   │   ├── format-utils.js         # Data formatting utilities
│   │   │   ├── crypto-utils.js         # Encryption/hashing utilities
│   │   │   ├── file-utils.js           # File processing utilities
│   │   │   └── constants.js            # Application constants
│   │   ├── lib/                         # Third-party libraries
│   │   │   ├── monaco-editor/          # Monaco editor files
│   │   │   ├── chart.js                # Chart.js library
│   │   │   ├── ethers.min.js           # Web3 library
│   │   │   ├── marked.min.js           # Markdown parser
│   │   │   ├── highlight.min.js        # Syntax highlighting
│   │   │   └── crypto-js.min.js        # Cryptography library
│   │   └── main.js                      # Main JavaScript entry point
│   │
│   ├── templates/                       # HTML templates (for SPA)
│   │   ├── layout/                      # Layout templates
│   │   │   ├── dashboard-layout.html   # Dashboard wrapper template
│   │   │   ├── auth-layout.html        # Authentication layout
│   │   │   └── modal-template.html     # Modal container template
│   │   ├── components/                  # Component templates
│   │   │   ├── sidebar.html            # Sidebar navigation
│   │   │   ├── navbar.html             # Top navigation bar
│   │   │   ├── chat-message.html       # Chat message template
│   │   │   ├── project-card.html       # Project card template
│   │   │   ├── file-item.html          # File list item
│   │   │   └── notification.html       # Notification template
│   │   └── pages/                       # Page templates
│   │       ├── dashboard-home.html     # Dashboard overview
│   │       ├── chat-interface.html     # Chat page template
│   │       ├── code-assistant.html     # Code assistant template
│   │       ├── document-qa.html        # Document Q&A template
│   │       ├── research-tools.html     # Research tools template
│   │       ├── notebook-editor.html    # Notebook template
│   │       ├── data-analysis.html      # Analysis template
│   │       ├── project-planner.html    # Kanban template
│   │       ├── citation-manager.html   # Citations template
│   │       └── user-settings.html      # Settings template
│   │
│   ├── config/                          # Configuration files
│   │   ├── webpack.config.js           # Webpack bundler config
│   │   ├── .eslintrc.js                # ESLint configuration
│   │   ├── .prettierrc                 # Prettier code formatting
│   │   └── build-config.js             # Build process configuration
│   │
│   ├── tests/                           # Frontend tests
│   │   ├── unit/                       # Unit tests
│   │   │   ├── components/             # Component tests
│   │   │   ├── services/               # Service tests
│   │   │   └── utils/                  # Utility tests
│   │   ├── integration/                # Integration tests
│   │   │   ├── auth-flow.test.js       # Authentication flow
│   │   │   ├── chat-flow.test.js       # Chat functionality
│   │   │   └── file-upload.test.js     # File operations
│   │   ├── e2e/                        # End-to-end tests
│   │   │   ├── cypress/                # Cypress test files
│   │   │   └── playwright/             # Playwright tests
│   │   └── fixtures/                   # Test data
│   │       ├── mock-api-responses.json
│   │       └── test-files/
│   │
│   ├── build/                           # Build output (generated)
│   │   ├── css/                        # Compiled CSS
│   │   ├── js/                         # Bundled JavaScript
│   │   └── assets/                     # Optimized assets
│   │
│   ├── package.json                     # Node.js dependencies for tooling
│   ├── .gitignore                      # Git ignore rules
│   └── README.md                       # Frontend documentation
│
├── backend/                            # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application entry
│   │   ├── config/                     # Configuration management
│   │   │   ├── __init__.py
│   │   │   ├── settings.py             # Application settings
│   │   │   ├── database.py             # Database configuration
│   │   │   └── security.py             # Security configurations
│   │   ├── api/                        # API endpoints
│   │   │   ├── __init__.py
│   │   │   └── v1/                     # API version 1
│   │   │       ├── __init__.py
│   │   │       ├── auth.py             # Authentication endpoints
│   │   │       ├── chat.py             # Chat/AI endpoints
│   │   │       ├── documents.py        # Document processing
│   │   │       ├── code.py             # Code execution endpoints
│   │   │       ├── research.py         # Research tools endpoints
│   │   │       ├── analysis.py         # Data analysis endpoints
│   │   │       ├── projects.py         # Project management
│   │   │       ├── files.py            # File management
│   │   │       ├── users.py            # User management
│   │   │       └── blockchain.py       # Blockchain endpoints
│   │   ├── models/                     # Data models
│   │   │   ├── __init__.py
│   │   │   ├── user.py                 # User model
│   │   │   ├── conversation.py         # Chat conversation model
│   │   │   ├── document.py             # Document model
│   │   │   ├── project.py              # Project model
│   │   │   ├── file.py                 # File model
│   │   │   └── citation.py             # Citation model
│   │   ├── schemas/                    # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py                 # User schemas
│   │   │   ├── auth.py                 # Auth request/response schemas
│   │   │   ├── chat.py                 # Chat schemas
│   │   │   ├── document.py             # Document schemas
│   │   │   └── common.py               # Common schemas
│   │   ├── services/                   # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py         # Authentication logic
│   │   │   ├── ai_service.py           # AI/LLM integration
│   │   │   ├── document_service.py     # Document processing
│   │   │   ├── code_service.py         # Code execution
│   │   │   ├── research_service.py     # Research tools
│   │   │   ├── file_service.py         # File operations
│   │   │   ├── blockchain_service.py   # Web3 integration
│   │   │   └── notification_service.py # Notifications
│   │   ├── agents/                     # LangChain AI agents
│   │   │   ├── __init__.py
│   │   │   ├── research_agent.py       # Research assistant agent
│   │   │   ├── code_review_agent.py    # Code review agent
│   │   │   ├── document_qa_agent.py    # Document Q&A agent
│   │   │   └── citation_agent.py       # Citation formatting agent
│   │   ├── core/                       # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── security.py             # Security utilities
│   │   │   ├── deps.py                 # Dependency injection
│   │   │   ├── exceptions.py           # Custom exceptions
│   │   │   └── middleware.py           # Custom middleware
│   │   ├── db/                         # Database layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # Base database class
│   │   │   ├── session.py              # Database session
│   │   │   └── repositories/           # Data access layer
│   │   │       ├── __init__.py
│   │   │       ├── user_repository.py
│   │   │       ├── chat_repository.py
│   │   │       └── document_repository.py
│   │   └── utils/                      # Utility functions
│   │       ├── __init__.py
│   │       ├── email.py                # Email utilities
│   │       ├── crypto.py               # Cryptographic utilities
│   │       ├── file_utils.py           # File processing
│   │       └── validators.py           # Data validation
│   ├── vector_store/                   # FAISS vector database
│   │   ├── __init__.py
│   │   ├── embeddings/                 # Generated embeddings
│   │   ├── indices/                    # FAISS index files
│   │   └── documents/                  # Processed documents
│   ├── sandbox/                        # Docker code execution
│   │   ├── Dockerfile                  # Sandbox container
│   │   ├── requirements.txt            # Sandbox dependencies
│   │   ├── runner.py                   # Code execution runner
│   │   └── security/                   # Security policies
│   │       ├── seccomp.json            # System call filtering
│   │       └── apparmor.profile        # AppArmor security profile
│   ├── migrations/                     # Database migrations
│   │   ├── alembic.ini                 # Alembic configuration
│   │   ├── env.py                      # Migration environment
│   │   ├── script.py.mako              # Migration template
│   │   └── versions/                   # Migration files
│   ├── tests/                          # Backend tests
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Test configuration
│   │   ├── unit/                       # Unit tests
│   │   │   ├── test_auth.py
│   │   │   ├── test_chat.py
│   │   │   └── test_documents.py
│   │   ├── integration/                # Integration tests
│   │   │   ├── test_api.py
│   │   │   └── test_agents.py
│   │   └── fixtures/                   # Test fixtures
│   │       ├── sample_documents/
│   │       └── mock_data.json
│   ├── requirements/                   # Python dependencies
│   │   ├── base.txt                    # Base requirements
│   │   ├── dev.txt                     # Development requirements
│   │   └── prod.txt                    # Production requirements
│   ├── Dockerfile                      # Backend container
│   ├── docker-compose.yml              # Local development setup
│   ├── .env.example                    # Environment variables template
│   ├── alembic.ini                     # Database migration config
│   ├── pytest.ini                     # Test configuration
│   └── README.md                       # Backend documentation
│
├── blockchain/                         # Blockchain components
│   ├── contracts/                      # Smart contracts
│   │   ├── AIMarketplace.sol          # AI model marketplace
│   │   ├── ContentProvenance.sol      # Content verification
│   │   ├── IdentityManager.sol        # Decentralized identity
│   │   └── AuditTrail.sol             # Activity logging
│   ├── scripts/                        # Deployment scripts
│   │   ├── deploy.js                  # Contract deployment
│   │   ├── verify.js                  # Contract verification
│   │   └── upgrade.js                 # Contract upgrades
│   ├── test/                          # Contract tests
│   │   ├── AIMarketplace.test.js
│   │   ├── ContentProvenance.test.js
│   │   └── IdentityManager.test.js
│   ├── artifacts/                     # Compiled contracts (generated)
│   ├── cache/                         # Hardhat cache (generated)
│   ├── hardhat.config.js              # Hardhat configuration
│   ├── package.json                   # Node.js dependencies
│   └── README.md                      # Blockchain documentation
│
├── infrastructure/                     # Infrastructure as Code
│   ├── docker/                        # Docker configurations
│   │   ├── frontend.Dockerfile        # Frontend container
│   │   ├── backend.Dockerfile         # Backend container
│   │   ├── nginx.Dockerfile           # Reverse proxy
│   │   └── docker-compose.prod.yml    # Production compose file
│   ├── kubernetes/                    # K8s manifests (future scaling)
│   │   ├── namespace.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── backend-deployment.yaml
│   │   ├── ingress.yaml
│   │   └── secrets.yaml
│   ├── terraform/                     # Cloud infrastructure
│   │   ├── main.tf                    # Main infrastructure
│   │   ├── variables.tf               # Input variables
│   │   ├── outputs.tf                 # Output values
│   │   └── modules/                   # Reusable modules
│   │       ├── database/
│   │       ├── storage/
│   │       └── networking/
│   └── nginx/                         # Web server configuration
│       ├── nginx.conf                 # Main nginx config
│       ├── sites-available/           # Available sites
│       └── ssl/                       # SSL certificates
│
├── scripts/                           # Development and deployment scripts
│   ├── setup/                         # Initial setup scripts
│   │   ├── install-deps.sh           # Install all dependencies
│   │   ├── setup-local-llm.sh        # Setup Phi-2 model
│   │   ├── init-db.sh                # Initialize database
│   │   ├── setup-blockchain.sh       # Setup local blockchain
│   │   └── dev-env.sh                # Development environment
│   ├── dev/                          # Development scripts
│   │   ├── start-dev.sh              # Start full development stack
│   │   ├── start-frontend.sh         # Frontend development server
│   │   ├── start-backend.sh          # Backend development server
│   │   ├── seed-data.sh              # Seed test data
│   │   ├── run-tests.sh              # Run all tests
│   │   ├── lint-code.sh              # Code linting
│   │   └── build-frontend.sh         # Build frontend for production
│   ├── deploy/                       # Deployment scripts
│   │   ├── deploy-frontend.sh        # Deploy to Vercel/Netlify
│   │   ├── deploy-backend.sh         # Deploy to Railway/Render
│   │   ├── deploy-contracts.sh       # Deploy smart contracts
│   │   ├── update-env.sh             # Update environment variables
│   │   └── backup-db.sh              # Database backup
│   └── utils/                        # Utility scripts
│       ├── generate-ssl.sh           # Generate SSL certificates
│       ├── clean-build.sh            # Clean build artifacts
│       └── health-check.sh           # Application health check
│
├── docs/                             # Documentation
│   ├── api/                          # API documentation
│   │   ├── openapi.json              # OpenAPI specification
│   │   └── endpoints.md              # Endpoint documentation
│   ├── architecture/                 # Architecture documentation
│   │   ├── overview.md               # System overview
│   │   ├── database-schema.md        # Database design
│   │   ├── api-design.md             # API design principles
│   │   └── security.md               # Security architecture
│   ├── deployment/                   # Deployment guides
│   │   ├── local-setup.md            # Local development setup
│   │   ├── production-deploy.md      # Production deployment
│   │   └── scaling.md                # Scaling considerations
│   ├── user-guides/                  # User documentation
│   │   ├── getting-started.md        # Getting started guide
│   │   ├── features.md               # Feature documentation
│   │   └── troubleshooting.md        # Common issues
│   └── development/                  # Developer guides
│       ├── contributing.md           # Contribution guidelines
│       ├── coding-standards.md       # Code style guide
│       └── testing.md                # Testing guidelines
│
├── data/                             # Data directory
│   ├── uploads/                      # User uploaded files
│   ├── models/                       # AI model files
│   │   └── embeddings/               # Embedding models
│   ├── exports/                      # Data exports
│   └── backups/                      # Database backups
│
├── config/                           # Global configuration files
│   ├── environments/                 # Environment-specific configs
│   │   ├── development.env          # Development environment
│   │   ├── staging.env              # Staging environment
│   │   └── production.env           # Production environment
│   ├── nginx/                       # Nginx configurations
│   │   ├── nginx.conf               # Main nginx config
│   │   └── ssl/                     # SSL certificates
│   └── monitoring/                  # Monitoring configurations
│       ├── prometheus.yml           # Prometheus config
│       └── grafana/                 # Grafana dashboards
│
├── .gitignore                       # Git ignore rules
├── .env.example                     # Environment variables template
├── docker-compose.yml               # Development Docker setup
├── docker-compose.prod.yml          # Production Docker setup
├── LICENSE                          # Project license
├── README.md                        # Project overview and setup
├── CHANGELOG.md                     # Version history and changes
├── CONTRIBUTING.md                  # Contribution guidelines
├── CODE_OF_CONDUCT.md              # Community guidelines
├── SECURITY.md                     # Security policy and reporting
└── package.json                    # Root package.json for workspace management