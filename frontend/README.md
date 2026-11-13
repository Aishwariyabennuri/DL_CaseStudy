# VestiAR frontend

The AI Fitting Room is an image-based workflow. Upload a full-body person
photo, select or upload a garment, choose its category, and request a result.
The backend runs the cloned `clothes-virtual-try-on` pipeline directly and
returns an explicit unavailable error when a compatible execution environment
is not available.

The frontend never receives provider credentials. Configure these only on the
backend:

- `VESTIAR_FITTING_REPOSITORY` (optional)
- `VESTIAR_FITTING_PYTHON` (optional)
- `VESTIAR_FITTING_ALLOW_CPU` (optional)

The backend passes multipart person and garment images to the existing
`/api/virtual-tryon` route, which invokes the repository's original
`run_pipeline()` entry point. Set the optional paths only when the repository
is not in its default project location. CPU execution is disabled by default
because the model is intended for CUDA-enabled environments.

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
