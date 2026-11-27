# Diagramas de la API Pokémon

Estos diagramas representan el código y el esquema de PostgreSQL de la versión final (Entrega III). GitHub renderiza los bloques Mermaid; para usarlos en la presentación se pueden exportar desde la vista renderizada.

## 1. Modelo de clases del dominio

Las multiplicidades se leen junto al nombre de cada clase: un Pokémon puede tener cero o un entrenador; un entrenador puede tener muchos Pokémon. Cada registro médico pertenece a un Pokémon y a un centro. La identidad de acceso (`Usuario`) está separada de las entidades de negocio: un usuario con rol `ENTRENADOR` no es lo mismo que un `Entrenador` del dominio.

~~~mermaid
classDiagram
    class Entrenador {
        +UUID id
        +str nombre
        +int nivel_experiencia
        +str region_origen
        +int medallas_obtenidas
    }
    class Pokemon {
        +UUID id
        +str nombre
        +TipoPokemon tipo_principal
        +int nivel
        +int puntos_vida
        +UUID? entrenador_id
    }
    class CentroPokemon {
        +UUID id
        +str nombre
        +str ciudad
        +int capacidad_maxima
        +bool en_servicio
    }
    class RegistroMedico {
        +UUID id
        +UUID pokemon_id
        +UUID centro_id
        +str diagnostico
        +date fecha_ingreso
        +EstadoAtencion estado
        +int costo
    }
    class TipoPokemon {
        <<enumeration>>
        FUEGO
        AGUA
        PLANTA
        ELECTRICO
    }
    class EstadoAtencion {
        <<enumeration>>
        EN_TRATAMIENTO
        DADO_DE_ALTA
    }
    class RolUsuario {
        <<enumeration>>
        ADMIN
        VETERINARIO
        ENTRENADOR
    }
    class Usuario {
        +UUID id
        +str email
        +str password_hash
        +str nombre_completo
        +RolUsuario rol
        +bool activo
        +int intentos_fallidos
        +datetime? bloqueado_hasta
        +int token_version
    }
    class RefreshToken {
        +UUID id
        +str token_hash
        +UUID usuario_id
        +datetime expira_en
        +bool revocado
        +datetime creado_en
        +str? familia_id
    }
    class PasswordResetToken {
        +UUID id
        +str token_hash
        +UUID usuario_id
        +datetime expira_en
        +bool usado
        +datetime creado_en
    }

    Usuario "1" -- "0..*" RefreshToken : posee
    Usuario "1" -- "0..*" PasswordResetToken : solicita
    Usuario --> RolUsuario : rol
    Entrenador "0..1" -- "0..*" Pokemon : asigna
    Pokemon "1" -- "0..*" RegistroMedico : tiene
    CentroPokemon "1" -- "0..*" RegistroMedico : atiende
    Pokemon --> TipoPokemon : tipo_principal
    RegistroMedico --> EstadoAtencion : estado
~~~

Las entidades del dominio están en `app/domain/models.py`. Los DTO de entrada y salida están en `app/schemas/schemas.py` (negocio) y `app/schemas/auth_schemas.py` (autenticación); ninguno devuelve `password` ni `password_hash`.

`token_version` se incrementa al restablecer la contraseña: todo access token emitido con la versión anterior deja de ser aceptado. `familia_id` agrupa los refresh de una misma sesión para revocarla completa si se reutiliza un refresh ya consumido.

## 2. Modelo de datos persistentes

PK indica clave primaria y FK indica clave foránea. La FK `entrenador_id` es opcional; `pokemon_id` y `centro_id` son obligatorias. Las tablas de autenticación usan `ON DELETE CASCADE` hacia `usuarios`. PostgreSQL aplica todas las claves foráneas.

~~~mermaid
erDiagram
    usuarios ||--o{ refresh_tokens : genera
    usuarios ||--o{ password_reset_tokens : solicita
    usuarios ||--o{ auth_sessions : abre
    auth_sessions |o--o{ refresh_tokens : agrupa
    entrenadores |o--o{ pokemones : asigna
    pokemones ||--o{ registros_medicos : recibe
    centros_pokemon ||--o{ registros_medicos : atiende

    usuarios {
        string id PK
        string email "unique"
        string password_hash "Argon2id"
        string nombre_completo
        string rol
        boolean activo
        int intentos_fallidos
        datetime bloqueado_hasta "nullable"
        int token_version
    }
    auth_sessions {
        string id PK
        string usuario_id FK
        boolean revocada
        datetime expira_en
    }
    refresh_tokens {
        string id PK
        string token_hash "SHA-256, unique"
        string usuario_id FK
        string familia_id FK "nullable"
        datetime expira_en
        boolean revocado
        datetime creado_en
    }
    password_reset_tokens {
        string id PK "jti del JWT"
        string token_hash "unique"
        string usuario_id FK
        datetime expira_en
        boolean usado
        datetime creado_en
    }
    auth_rate_limits {
        string clave PK
        int intentos
    }
    entrenadores {
        string id PK
        string nombre
        int nivel_experiencia
        string region_origen
        int medallas_obtenidas
    }
    pokemones {
        string id PK
        string nombre
        string tipo_principal
        int nivel
        int puntos_vida
        string entrenador_id FK "nullable"
    }
    centros_pokemon {
        string id PK
        string nombre
        string ciudad
        int capacidad_maxima
        boolean en_servicio
    }
    registros_medicos {
        string id PK
        string pokemon_id FK
        string centro_id FK
        string diagnostico
        date fecha_ingreso
        string estado
        int costo
    }
~~~

El esquema lo define `app/infrastructure/models.py` y lo crean tres migraciones versionadas de Alembic, aplicadas en orden:

| Revisión | Contenido |
|---|---|
| `4629db295117` | Tablas de negocio: `entrenadores`, `pokemones`, `centros_pokemon`, `registros_medicos` |
| `b71d8e12a45c` | `usuarios`, `refresh_tokens` y `password_reset_tokens` |
| `c92ef03a6d10` | `token_version`, `auth_sessions`, `familia_id` en `refresh_tokens` y `auth_rate_limits` |

`auth_rate_limits` no tiene FK: guarda contadores por clave (`reset-ip:<ip>`, `reset-email:<correo>`, `reset-confirm:<ip>`) para limitar la recuperación sin bloquear la cuenta.

## 3. Capas y recorrido de una petición protegida

Ejemplo: `POST /centros-pokemon/` con rol `VETERINARIO`. FastAPI lee el Bearer, `get_current_user` valida el JWT y la sesión, `require_roles` decide el permiso (403 si no corresponde), el DTO `CrearCentroPokemon` valida el cuerpo y el servicio aplica las reglas antes de que el repositorio guarde en PostgreSQL.

~~~mermaid
flowchart LR
    Cliente["Cliente / Swagger"] --> Router["Router HTTP<br/>app/routers"]
    Router --> DTO["DTO y validación<br/>app/schemas"]
    Router --> DI["Depends<br/>app/core/dependencies.py"]
    DI --> Auth["get_current_user<br/>401 si falla"]
    Auth --> Tokens["Firma y validación JWT<br/>app/security/tokens.py"]
    Router --> Permisos["require_roles<br/>app/security/permissions.py<br/>403 si falla"]
    Permisos --> Auth
    DI --> Sesion["get_db / Session<br/>app/infrastructure/database.py"]
    DI --> Servicio["Caso de uso<br/>app/services"]
    DTO --> Servicio
    Servicio --> Dominio["Entidades y reglas<br/>app/domain"]
    Servicio --> Repositorio["Repositorio SQLAlchemy<br/>app/repositories"]
    Servicio --> Seguridad["Argon2id y correo<br/>app/security/passwords.py<br/>app/security/mail.py"]
    Sesion --> Repositorio
    Repositorio --> Mapper["Mapper<br/>app/infrastructure/mappers.py"]
    Mapper --> Dominio
    Repositorio --> ORM["Modelo ORM<br/>app/infrastructure/models.py"]
    ORM --> PG[(PostgreSQL)]
~~~

La respuesta recorre el camino inverso desde PostgreSQL hasta el cliente. Los errores de negocio se convierten en la respuesta JSON uniforme en `app/core/handlers.py`; el dominio no conoce códigos HTTP. Alembic prepara las tablas al iniciar el contenedor; el seeder inserta datos de demostración sin duplicarlos.

## 4. Ciclo de sesión: login, refresh y logout

~~~mermaid
sequenceDiagram
    participant C as Cliente
    participant R as auth_router
    participant S as AuthService
    participant T as TokenRepository
    participant DB as PostgreSQL

    C->>R: POST /auth/login (email, password)
    R->>S: login()
    S->>DB: buscar usuario y verificar Argon2id
    alt credenciales incorrectas
        S->>DB: intentos_fallidos + 1 (5 fallos = bloqueo 15 min)
        S-->>C: 401 genérico, sin tokens
    else correctas
        S->>T: guardar_sesion (auth_sessions + hash del refresh)
        S-->>C: access JWT (30 s, type=access, sid) + refresh opaco
    end
    C->>R: POST /auth/refresh (refresh)
    R->>S: refresh()
    S->>T: rotar(): si está vigente, lo marca como consumido y guarda el nuevo
    alt refresh ya consumido (reutilización)
        T->>DB: revoca toda la familia (auth_sessions.revocada = true)
        S-->>C: 401
    else vigente
        S-->>C: nuevo par access + refresh
    end
    C->>R: POST /auth/logout (refresh)
    R->>S: logout()
    S->>T: cerrar_sesion(): revoca la sesión y sus refresh
    S-->>C: 204 (el access de esa sesión también deja de servir)
~~~

## 5. Recuperación de contraseña

~~~mermaid
sequenceDiagram
    participant C as Cliente
    participant S as AuthService
    participant T as TokenRepository
    participant M as Mailpit (SMTP de prueba)

    C->>S: POST /auth/forgot-password (email)
    S->>T: limitar por IP y por correo (auth_rate_limits)
    S->>T: preparar_recuperacion (guarda jti y hash del JWT)
    S->>M: correo con enlace (token en el fragmento #)
    S-->>C: 202 genérico, exista o no la cuenta
    C->>S: POST /auth/reset-password (token, password nueva)
    S->>S: validar firma, algoritmo, exp, sub, type=password_reset, ver
    S->>T: consumir_recuperacion en una transacción
    Note over T: bloquea la fila del usuario (UPDATE) y comprueba usado = false<br/>nuevo hash Argon2id, token_version + 1<br/>revoca sesiones, refresh y otros resets pendientes
    alt token alterado, vencido, de otro propósito o ya usado
        S-->>C: 401 y la contraseña no cambia
    else válido
        S-->>C: 200 "Contraseña actualizada. Inicia sesión nuevamente."
    end
~~~

La cuenta objetivo se obtiene del `sub` del JWT validado; el cuerpo de la petición no acepta un ID de usuario, por lo que no se puede cambiar la contraseña de otra cuenta.
