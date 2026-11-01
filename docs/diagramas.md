# Diagramas de la API Pokémon

Estos diagramas representan el código y el esquema de SQLite de esta versión. GitHub renderiza los bloques Mermaid; para usarlos en la presentación se pueden exportar desde la vista renderizada.

## 1. Modelo de clases del dominio

Las multiplicidades se leen junto al nombre de cada clase: un Pokémon puede tener cero o un entrenador; un entrenador puede tener muchos Pokémon. Cada registro médico pertenece a un Pokémon y a un centro.

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

    Entrenador "0..1" -- "0..*" Pokemon : asigna
    Pokemon "1" -- "0..*" RegistroMedico : tiene
    CentroPokemon "1" -- "0..*" RegistroMedico : atiende
    Pokemon --> TipoPokemon : tipo_principal
    RegistroMedico --> EstadoAtencion : estado
~~~

Las entidades del dominio están en app/domain/models.py. Los DTO de entrada y salida están en app/schemas/schemas.py.

## 2. Modelo de datos persistentes

PK indica clave primaria y FK indica clave foránea. La FK entrenador_id es opcional; pokemon_id y centro_id son obligatorias. SQLite aplica las claves foráneas al abrir las conexiones de la API.

~~~mermaid
erDiagram
    entrenadores |o--o{ pokemones : asigna
    pokemones ||--o{ registros_medicos : recibe
    centros_pokemon ||--o{ registros_medicos : atiende

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

El esquema lo define app/infrastructure/models.py y lo crea la migración versionada de Alembic en migrations/versions/.

## 3. Capas y recorrido de una petición

Ejemplo: POST /entrenadores/. FastAPI valida el cuerpo con CrearEntrenador, resuelve un EntrenadorService para esa petición y le entrega repositorios que comparten la misma sesión. El repositorio guarda el modelo ORM; el mapper convierte la fila al modelo de dominio; el router responde con EntrenadorResponse.

~~~mermaid
flowchart LR
    Cliente["Cliente / Swagger"] --> Router["Router HTTP<br/>app/routers"]
    Router --> DTO["DTO y validación<br/>app/schemas"]
    Router --> DI["Depends<br/>app/core/dependencies"]
    DI --> Sesion["get_db / Session<br/>app/infrastructure/database"]
    DI --> Servicio["Caso de uso<br/>app/services"]
    DTO --> Servicio
    Servicio --> Dominio["Entidades y reglas<br/>app/domain"]
    Servicio --> Repositorio["Repositorio SQLAlchemy<br/>app/repositories"]
    Sesion --> Repositorio
    Repositorio --> Mapper["Mapper<br/>app/infrastructure/mappers.py"]
    Mapper --> Dominio
    Repositorio --> ORM["Modelo ORM<br/>app/infrastructure/models"]
    ORM --> SQLite[(SQLite)]
~~~

La respuesta recorre el camino inverso desde SQLite hasta el cliente. Alembic prepara las tablas antes del primer uso; el seeder inserta datos de demostración.
