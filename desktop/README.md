# Lunt Desktop App

Aplicación de escritorio para Lunt usando Tauri 2.0, que permite ejecutar la interfaz web como una aplicación nativa en Windows, macOS y Linux.

## 🎯 Características

- **Multiplataforma**: Windows, macOS, Linux
- **Ligera**: ~5-10 MB de instalador (vs ~100+ MB de Electron)
- **Rendimiento**: Usa WebView nativo del sistema operativo
- **Seguridad**: Sandboxing y CSP integrados
- **Futuro**: Cache SQLite local para modo offline (TODO)

## 📋 Requisitos

### Sistema

- **Windows**: Windows 10 1903+ (build 18362+)
- **macOS**: macOS 10.15+ (Catalina o superior)
- **Linux**: Depende de la distribución, requiere WebKitGTK

### Desarrollo

- **Rust**: 1.70+
- **Node.js**: 22+ (para compilar el frontend)
- **System Dependencies**:
  - **Linux**: 
    ```bash
    sudo apt-get update
    sudo apt-get install -y \
      libwebkit2gtk-4.1-dev \
      build-essential \
      curl \
      wget \
      file \
      libxdo-dev \
      libssl-dev \
      libayatana-appindicator3-dev \
      librsvg2-dev
    ```
  - **macOS**: Xcode Command Line Tools
    ```bash
    xcode-select --install
    ```
  - **Windows**: Visual Studio 2022 con C++ Build Tools

## 🚀 Build Instructions

### 1. Setup del Entorno

#### Instalar Rust

```bash
# Unix/Linux/macOS
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Windows
# Descargar e instalar desde: https://rustup.rs/
```

#### Verificar Instalación

```bash
rustc --version
cargo --version
```

### 2. Instalar Dependencias del Frontend

```bash
cd web
npm install
cd ..
```

### 3. Development Mode

```bash
cd desktop
cargo tauri dev
```

Esto:
1. Compila el frontend en modo desarrollo (`npm run dev`)
2. Inicia el servidor de desarrollo en `http://localhost:3000`
3. Abre la aplicación Tauri apuntando al servidor

**Hot Reload**: Los cambios en el frontend se reflejan automáticamente.

### 4. Production Build

#### Build para la Plataforma Actual

```bash
cd desktop
cargo tauri build
```

Esto:
1. Compila el frontend en modo producción (`npm run build` en `web/`)
2. Empaqueta el resultado en `web/dist/`
3. Compila el binario de Rust
4. Crea instaladores nativos

#### Outputs

Los binarios generados están en:

- **Linux**: 
  - `desktop/src-tauri/target/release/bundle/deb/lunt_0.1.0_amd64.deb`
  - `desktop/src-tauri/target/release/bundle/appimage/lunt_0.1.0_amd64.AppImage`
- **macOS**:
  - `desktop/src-tauri/target/release/bundle/macos/Lunt.app`
  - `desktop/src-tauri/target/release/bundle/dmg/Lunt_0.1.0_x64.dmg`
- **Windows**:
  - `desktop/src-tauri/target/release/bundle/msi/Lunt_0.1.0_x64.msi`
  - `desktop/src-tauri/target/release/bundle/nsis/Lunt_0.1.0_x64-setup.exe`

### 5. Cross-Platform Builds (Avanzado)

Para compilar para otras plataformas, necesitas herramientas específicas:

#### Linux → Windows (Wine + MinGW)

```bash
rustup target add x86_64-pc-windows-gnu
cargo tauri build --target x86_64-pc-windows-gnu
```

#### macOS → Linux (Docker)

```bash
# Requiere Docker y configuración compleja
# Ver: https://tauri.app/v1/guides/building/cross-platform/
```

**Recomendación**: Usar CI/CD para builds multiplataforma (GitHub Actions).

## 📂 Estructura del Proyecto

```
desktop/
├── src-tauri/
│   ├── src/
│   │   ├── main.rs          # Entry point de la aplicación
│   │   └── lib.rs           # Módulo de biblioteca (Tauri commands)
│   ├── build.rs             # Build script de Cargo
│   ├── Cargo.toml           # Dependencias de Rust
│   ├── tauri.conf.json      # Configuración de Tauri
│   └── icons/               # Iconos de la aplicación (TODO: crear)
│       ├── 32x32.png
│       ├── 128x128.png
│       ├── icon.icns        # macOS
│       └── icon.ico         # Windows
└── README.md                # Este archivo
```

## ⚙️ Configuración

### tauri.conf.json

Archivo principal de configuración. Puntos clave:

- **`build.frontendDist`**: Ruta al build del frontend (`../web/dist`)
- **`build.beforeBuildCommand`**: Comando para compilar el frontend
- **`app.windows`**: Configuración de la ventana (tamaño, título, etc.)
- **`app.security.csp`**: Content Security Policy
- **`bundle.targets`**: Plataformas objetivo (`"all"` = todas)

### Cargo.toml

Dependencias de Rust:

- `tauri`: Framework principal
- `tauri-plugin-shell`: Plugin para ejecutar comandos del sistema
- `serde`: Serialización/deserialización JSON
- **Profile release**: Optimizaciones para producción (LTO, strip, opt-level)

## 🔧 Desarrollo

### Añadir Tauri Commands

Los "commands" son funciones de Rust que puedes llamar desde JavaScript:

```rust
// En src-tauri/src/main.rs o lib.rs

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

Llamar desde JavaScript:

```typescript
import { invoke } from '@tauri-apps/api/core';

const greeting = await invoke('greet', { name: 'World' });
console.log(greeting); // "Hello, World!"
```

### Debug Tools

En modo desarrollo, la ventana abre automáticamente las DevTools.

Para producción, puedes habilitar con `Ctrl+Shift+I` si compilas con feature `devtools`.

## 🚧 TODO: Modo Offline con SQLite

**Objetivo**: Permitir que la aplicación desktop funcione sin conexión usando cache local.

### Plan de Implementación

1. **Agregar dependencias**:
   ```toml
   [dependencies]
   rusqlite = "0.30"
   tokio = { version = "1", features = ["full"] }
   ```

2. **Crear esquema SQLite**:
   - Tablas para concepts, insumos, prices (espejo de PostgreSQL)
   - Metadata de sincronización (last_sync, dirty_records)

3. **Implementar Commands**:
   ```rust
   #[tauri::command]
   async fn sync_data() -> Result<SyncStatus, String>
   
   #[tauri::command]
   async fn get_concepts_offline() -> Result<Vec<Concept>, String>
   ```

4. **Lógica de Sync**:
   - Al abrir app: verificar conectividad
   - Si online: sync desde API → SQLite
   - Si offline: usar datos de SQLite
   - Conflictos: timestamp wins o manual merge

5. **UI Indicators**:
   - Badge "Offline Mode" en la app
   - Indicador de sincronización en progreso
   - Alertas de cambios pendientes

6. **Ubicación del DB**:
   ```rust
   use tauri::api::path::app_data_dir;
   
   let db_path = app_data_dir(&config)?.join("lunt.db");
   ```

### Referencias

- [Tauri State Management](https://tauri.app/v1/guides/features/command/#accessing-managed-state)
- [Rusqlite Docs](https://docs.rs/rusqlite/)
- [Offline-First Patterns](https://developers.google.com/web/fundamentals/instant-and-offline/offline-cookbook)

## 🐛 Troubleshooting

### Error: "webkit2gtk not found" (Linux)

```bash
sudo apt-get install libwebkit2gtk-4.1-dev
```

### Error: "cargo not found"

Instala Rust: https://rustup.rs/

### Error: "frontend build failed"

```bash
cd ../web
npm install
npm run build
cd ../desktop
```

### Error: "tauri: command not found"

```bash
cargo install tauri-cli --version "^2.0.0"
```

### Build muy lento

Desactiva optimizaciones en desarrollo:

```toml
[profile.dev]
opt-level = 0
```

## 📚 Recursos

- [Tauri Docs](https://tauri.app/)
- [Tauri Examples](https://github.com/tauri-apps/tauri/tree/dev/examples)
- [Tauri Discord](https://discord.gg/tauri)
- [Rust Book](https://doc.rust-lang.org/book/)

## 📝 Notas

- **Iconos**: Por crear. Puedes generarlos con https://tauri.app/v1/guides/features/icons
- **Code Signing**: Necesario para distribución en macOS/Windows (ver docs de Tauri)
- **Auto-update**: Requiere configuración adicional con Tauri Updater plugin
- **CI/CD**: GitHub Actions puede compilar para las 3 plataformas simultáneamente

---

**Última actualización**: 2025-10-28  
**Versión Tauri**: 2.0  
**Versión App**: 0.1.0
