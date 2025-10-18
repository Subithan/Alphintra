## Gateway Environment Variables

The frontend now proxies all backend access through the service gateway. Configure the endpoint before running local commands:

```bash
cp .env.example .env.local
echo "NEXT_PUBLIC_GATEWAY_URL=http://localhost:8080" >> .env.local
npm run dev
```

Mobile builds expect the equivalent Expo variable:

```bash
cp ../mobile/.env.example ../mobile/.env
echo "EXPO_PUBLIC_GATEWAY_URL=https://api.alphintra.dev" >> ../mobile/.env
```

Architecting "Alphintra": A Comprehensive Guide to Immersive Web Experiences with Three.js and GSAPPart I: Foundational Architecture - Setting the StageThe creation of a sophisticated, interactive web platform like Alphintra demands an architectural foundation that is both robust and scalable. The choice of technologies and the structure of the project are not merely preliminary steps; they are critical decisions that dictate the application's performance, maintainability, and capacity for future expansion. This section outlines the establishment of a modern development environment, prioritizing a component-based architecture with React and React Three Fiber, which represents the industry standard for building complex and manageable Three.js projects.Section 1.1: Project Scaffolding and Environment SetupA modern development workflow begins with a fast and efficient build tool. Vite stands out for its near-instantaneous hot module replacement (HMR) and optimized build process, making it an ideal choice for a project that will involve rapid iteration on both 2D UI and 3D scenes.Core Concept: Establishing a Modern Development EnvironmentThe initial setup involves scaffolding a new project and carefully integrating the core libraries. A centralized configuration for animation plugins is a key practice to ensure consistency and avoid redundant code.Implementation DetailsThe project begins by scaffolding a new React application with TypeScript support using Vite. This provides a solid, type-safe foundation.Bashnpm create vite@latest alphintra-landing -- --template react-ts
cd alphintra-landing
With the project created, the next step is to install the essential dependencies for building the 3D experience. React Three Fiber (R3F) and its companion library, Drei, are indispensable. R3F provides a declarative, component-based syntax for Three.js, which dramatically simplifies scene management and aligns with modern web development practices by allowing developers to treat 3D objects as reusable React components. Drei offers a vast collection of helpers, abstractions, and ready-made components that accelerate development.3Bashnpm install three @react-three/fiber @react-three/drei
Simultaneously, the GreenSock Animation Platform (GSAP) and its React-specific package are installed. The @gsap/react package provides the useGSAP hook, which is critical for managing animations within React's component lifecycle. This hook automatically handles the cleanup of tweens and timelines when a component unmounts, a crucial feature for preventing memory leaks and ensuring stable performance in single-page applications.4Bashnpm install gsap @gsap/react
Certain advanced GSAP features are provided as plugins and must be explicitly registered with the GSAP core before use.6 For the Alphintra project, ScrollTrigger (for scroll-based animations) and SplitText (for advanced typography effects) are essential. To maintain a clean and organized codebase, these plugins should be registered in a single, centralized configuration file. This approach prevents the need to import and register them in every component where they are used.5Example gsap.config.ts:TypeScriptimport { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText"; // Note: SplitText is a premium plugin

// Register plugins only in a client-side environment
if (typeof window!== "undefined") {
  gsap.registerPlugin(ScrollTrigger, SplitText);
}

export { gsap, ScrollTrigger, SplitText };
This configuration ensures that a single, consistent instance of GSAP and its plugins is used throughout the application, promoting modularity and simplifying maintenance.Section 1.2: The Three.js Trinity - Scene, Camera, and RendererAt the heart of any Three.js application lie three essential components: the scene, the camera, and the renderer. The scene acts as a container for all 3D objects, lights, and cameras. The camera defines the viewpoint from which the scene is observed. The renderer is responsible for taking the scene and camera information and drawing the resulting 2D image onto an HTML <canvas> element.7Core Concept: Declarative Scene Management with React Three FiberIn a traditional Three.js setup, these components are created and managed imperatively. However, React Three Fiber abstracts this process into a declarative model, primarily through its <Canvas> component. This shift from imperative commands (scene.add(mesh)) to a declarative, state-driven structure (<My3DComponent />) is more than a convenience; it is a fundamental architectural choice. It allows the 3D scene to be a direct reflection of the application's state, managed seamlessly by React. This component-based approach also enables better code organization, reusability, and integrates perfectly with GSAP's useGSAP hook for lifecycle-aware animations.4Implementation DetailsThe <Canvas> Component: The R3F <Canvas> component is the root of the 3D experience. It automatically creates the THREE.Scene and THREE.WebGLRenderer and manages the render loop.2 For the Alphintra project, it will be configured for optimal performance and to support the glassmorphism UI.JavaScriptimport { Canvas } from '@react-three/fiber';

function App() {
  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh' }}>
      <Canvas
        gl={{
          antialias: true,
          alpha: true, // Required for transparent background
        }}
        dpr={} // Clamp device pixel ratio for performance
      >
        {/* 3D Scene Components Go Here */}
      </Canvas>
      {/* HTML UI Components Go Here */}
    </div>
  );
}
Key configurations include:gl={{ alpha: true }}: This makes the renderer's background transparent, which is a prerequisite for the glassmorphism effect where HTML UI elements need to blur the 3D scene behind them.9dpr={}: This sets the device pixel ratio, clamping it at a maximum of 2. On high-resolution mobile devices, the DPR can be 3 or higher, which is computationally expensive. Limiting it provides a significant performance boost with a minimal loss in visual fidelity.10The Camera: The camera determines what the user sees. A PerspectiveCamera is most suitable for this project as it mimics human vision, where objects appear smaller as they move further away.8 Drei's <PerspectiveCamera> component makes this easy to implement and control.JavaScriptimport { PerspectiveCamera } from '@react-three/drei';

function Scene() {
  return (
    <>
      <PerspectiveCamera
        makeDefault // Sets this as the default camera for the scene
        fov={75}
        near={0.1}
        far={1000}
        position={} // Initial camera position
      />
      {/* Rest of the scene */}
    </>
  );
}
The initial camera position is crucial as it defines the starting point of the scroll-driven narrative. The fov (field of view), near, and far properties define the camera's viewing frustum—the region of 3D space that will be rendered.12Section 1.3: Illuminating the Scene - Professional LightingLighting is a fundamental element of 3D rendering that transforms a collection of flat shapes into a believable, immersive world. It is not an afterthought but a core component of the design process. Proper lighting adds depth, defines form, creates mood, and is essential for making materials look realistic.13Core Concept: Layered Lighting for Realism and PerformanceA professional lighting setup typically involves multiple layers of light working in concert. This includes a base ambient light for global illumination, a primary directional light to act as a key light source and cast shadows, and image-based lighting via an environment map for realistic reflections and ambient tones.Implementation DetailsAmbient and Directional Lights:Ambient Light: An <ambientLight> provides a soft, uniform light that illuminates the entire scene from all directions. Its primary purpose is to fill in shadows so they are not completely black, adding a baseline level of visibility. An intensity of around 0.5 is often a good starting point.13Directional Light: A <directionalLight> simulates a distant light source, like the sun, where all light rays are parallel. It is ideal for creating strong, defined shadows, which are crucial for adding depth and realism to the scene. Configuring its position determines the direction of the light and the angle of the shadows. Enabling castShadow on the light is the first step in the shadow-casting process.12Environment Mapping for High-Fidelity Reflections:For the highest level of realism, especially on metallic or reflective surfaces, image-based lighting is a powerful and performant technique. Drei's <Environment> component simplifies this process significantly. It loads a high-dynamic-range (HDR) image and uses it to light the entire scene, providing nuanced, realistic reflections and ambient color that would be very difficult and computationally expensive to achieve with multiple traditional lights.2JavaScriptimport { AmbientLight, DirectionalLight } from 'three';
import { Environment } from '@react-three/drei';
import { Suspense } from 'react';

function SceneLighting() {
  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight
        castShadow
        position={}
        intensity={1.5}
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      <Suspense fallback={null}>
        {/* Use an HDR file for realistic environment lighting */}
        <Environment files="/path/to/your/environment.hdr" />
      </Suspense>
    </>
  );
}
This layered approach—combining a soft ambient fill, a strong directional key light with shadows, and a detailed environment map—creates a dynamic and visually rich scene that forms the perfect canvas for the Alphintra landing page.Part II: Crafting the 3D World of AlphintraWith the foundational architecture in place, the focus shifts to creating the specific 3D elements that will define the Alphintra brand experience. This involves a strategic blend of procedural generation for dynamic backgrounds and a structured, data-driven approach for the hero element—the interactive 3D trading chart. This hybrid methodology balances creative flexibility with the stringent performance requirements of a modern web application.Section 2.1: Designing the Immersive BackgroundThe background of the Alphintra landing page should not be a static backdrop but a dynamic, living environment that subtly reinforces the themes of data, technology, and finance. A field of interactive particles or abstract data constructs can create a sense of depth and complexity without distracting from the main content.Core Concept: Procedural and Instanced Backgrounds for PerformanceTo render thousands of background elements without compromising performance, two key techniques are employed: particle systems for vast numbers of simple points and instancing for repeating geometries. Animation is offloaded to the GPU via custom shaders, ensuring the main thread remains free for user interactions.Implementation DetailsParticle Systems:A particle system is an efficient way to render a massive number of points. Using Drei's <Points> component, a custom BufferGeometry can be created to define the initial positions of thousands of particles, arranging them in a grid, sphere, or any other desired shape. This forms a vast, data-like space that serves as the canvas for the background.13Instancing for Performance:When the background requires repeating geometric shapes (e.g., small cubes or abstract glyphs) instead of simple points, InstancedMesh is the most performant solution. Instancing allows the GPU to render thousands of copies of a single geometry and material in a single draw call. This drastically reduces CPU overhead and is a critical optimization technique for maintaining a high frame rate in complex scenes.18Shader-Based Animation:To animate thousands of particles or instances smoothly, the animation logic must be executed on the GPU. This is achieved through custom shaders. A simple vertex shader can be written to modify the position of each particle or instance on every frame. By passing a uTime uniform (a value that increments over time) to the shader, a continuous, subtle motion like a gentle drift or wave can be created. This approach is orders of magnitude more performant than attempting to update each object's position individually using JavaScript on the CPU.18Example Particle Field with Shader Animation:JavaScriptimport * as THREE from 'three';
import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Points } from '@react-three/drei';

const particleShaderMaterial = new THREE.ShaderMaterial({
  uniforms: {
    uTime: { value: 0.0 },
    uSize: { value: 2.0 }
  },
  vertexShader: `
    uniform float uTime;
    uniform float uSize;
    void main() {
      vec3 pos = position;
      pos.y += sin(pos.x * 10.0 + uTime) * 0.1;
      vec4 modelPosition = modelMatrix * vec4(pos, 1.0);
      vec4 viewPosition = viewMatrix * modelPosition;
      gl_Position = projectionMatrix * viewPosition;
      gl_PointSize = uSize;
    }
  `,
  fragmentShader: `
    void main() {
      gl_FragColor = vec4(1.0, 1.0, 1.0, 0.5);
    }
  `,
  transparent: true,
  blending: THREE.AdditiveBlending,
  depthWrite: false,
});

function ParticleBackground() {
  const pointsRef = useRef();
  const count = 5000;

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count * 3; i++) {
      pos[i] = (Math.random() - 0.5) * 20;
    }
    return pos;
  }, [count]);

  useFrame((state) => {
    pointsRef.current.material.uniforms.uTime.value = state.clock.elapsedTime;
  });

  return (
    <Points ref={pointsRef} positions={positions} material={particleShaderMaterial} />
  );
}
Section 2.2: Modeling and Implementing the 3D Trading ChartThe 3D trading chart is the centerpiece of the landing page. It must be visually striking and immediately recognizable as a representation of financial data. Building this element procedurally within Three.js allows for potential dynamic data integration and provides complete control over its appearance and animation.Core Concept: Procedural Geometry for Data VisualizationThe chart is constructed by combining primitive Three.js geometries. This procedural approach allows the chart's form to be driven by data arrays, making it a flexible and powerful visualization tool.Implementation DetailsGeometries for Chart Elements:Bar Charts: THREE.BoxGeometry is perfect for creating the bars. The height of each box can be directly mapped to a data point in an array.Line Graphs: For line graphs, a THREE.CatmullRomCurve3 can be created from an array of THREE.Vector3 data points. This smooth curve can then be used as the path for a THREE.TubeGeometry, creating a clean, continuous line.15Materials for a Polished Look:THREE.MeshStandardMaterial is an excellent choice for the chart elements, as it responds realistically to the scene's lighting, giving the objects a solid, physical appearance. For a more futuristic or high-tech aesthetic, THREE.MeshPhysicalMaterial can be used. It extends MeshStandardMaterial with advanced properties like transmission and thickness, which can be used to create compelling glass or translucent plastic effects, tying the 3D elements thematically to the UI's glassmorphism design.18Immersive 3D Text:To add labels, axes, and data callouts, Drei's <Text> component is the ideal solution. It uses the high-performance Troika Text library to render crisp, legible text directly within the 3D scene. This is far more immersive than overlaying HTML elements and ensures that the text is properly occluded by and integrated with other 3D objects.1Example 3D Bar Chart Component:JavaScriptimport * as THREE from 'three';
import { Text } from '@react-three/drei';

const data = ;

function TradingChart() {
  return (
    <group position={[-data.length / 2, 0, 0]}>
      {data.map((value, index) => (
        <mesh key={index} position={[index * 1.5, value / 2, 0]}>
          <boxGeometry args={[1, value, 1]} />
          <meshStandardMaterial color="#4a90e2" />
        </mesh>
      ))}
      <Text position={[0, -1, 0]} fontSize={0.5} color="white">
        Market Performance
      </Text>
    </group>
  );
}
Section 2.3: Asset Optimization WorkflowWeb performance is a non-negotiable aspect of modern web development. Raw 3D assets exported from modeling software like Blender are often far too large and complex for real-time rendering in a browser. A dedicated optimization pipeline is essential to transform these assets into lightweight, performant files suitable for the web.24Core Concept: A Multi-Stage Pipeline for Web-Ready 3D AssetsThe optimization process involves several stages, from initial modeling considerations to final compression, ensuring that assets are as small and efficient as possible without sacrificing essential visual quality.Implementation DetailsModeling in Blender:The process starts in the 3D modeling software. Best practices include:Low-Poly Modeling: Creating models with the lowest possible polygon count necessary to achieve the desired silhouette. Every triangle adds to the rendering cost.19Decimation: Using Blender's "Decimate" modifier to intelligently reduce the polygon count of an existing high-poly model while preserving its overall shape.19Texture Baking:Real-time lighting and shadows are among the most computationally expensive parts of 3D rendering. For static objects, this lighting can be pre-calculated in Blender and "baked" into a texture map. This includes ambient occlusion (AO), which adds soft contact shadows, and even the full lighting information. This technique dramatically reduces the real-time rendering load, as the GPU only needs to display a texture instead of calculating complex light interactions on the fly.11glTF and Draco Compression:The glTF (GL Transmission Format) is the "JPEG of 3D." It is a file format designed specifically for the efficient transmission and loading of 3D scenes and models by applications.24 When exporting from Blender, selecting the glTF format is the first step. To further reduce file size, Draco compression should be applied. Draco is a library for compressing and decompressing 3D geometric meshes and point clouds, and it can reduce the size of 3D models significantly with minimal visual degradation.27 R3F and Drei make loading these optimized assets trivial with the <Gltf> component, which handles the parsing and decoding automatically.This comprehensive approach to asset creation and optimization ensures that the 3D world of Alphintra is not only visually impressive but also highly performant and accessible across a wide range of devices.Part III: The Art of Motion - Animating with GSAPThis section bridges the gap between the static 3D world and the dynamic, animated experience. The GreenSock Animation Platform (GSAP) provides a powerful and intuitive API for creating fluid, high-performance animations. Its core strength lies in its ability to animate any numeric property of any JavaScript object, making it a perfect tool for manipulating the properties of Three.js objects.Section 3.1: GSAP Core Principles - Tweens and TimelinesGSAP's animation system is built upon two fundamental concepts: Tweens and Timelines. A "Tween" is a single animation instance—the movement of one or more properties from a starting state to an ending state over a period of time. A "Timeline" is a powerful container for sequencing and synchronizing multiple tweens, allowing for the creation of complex, choreographed animation sequences.28Core Concept: Animating Three.js Object PropertiesA crucial distinction when animating with GSAP in a Three.js context, as opposed to the DOM, is the target of the animation. Instead of targeting the 3D object (the THREE.Mesh) directly for properties like position or rotation, the animation must target the specific property object itself (e.g., mesh.position, mesh.rotation, mesh.scale). These properties are objects (Vector3 or Euler) that contain the numeric values (x, y, z) that GSAP can interpolate.15 Animating mesh.position is significantly more performant than animating CSS top or left on a DOM element, as it doesn't trigger browser layout recalculations.30Implementation DetailsTweens:A tween is created using one of GSAP's core methods: gsap.to(), gsap.from(), or gsap.fromTo().31 For example, to animate a mesh's position and scale, the code would target mesh.position and mesh.scale respectively.JavaScriptimport { useGSAP } from '@gsap/react';
import { useRef } from 'react';
import { Mesh } from 'three';

function AnimatedCube() {
  const meshRef = useRef<Mesh>(null);

  useGSAP(() => {
    if (!meshRef.current) return;

    // Animate the mesh's position from its current state TO x: 5
    gsap.to(meshRef.current.position, {
      x: 5,
      duration: 2,
      ease: 'power2.inOut',
    });

    // Animate the mesh's scale FROM a scale of 0 TO its current scale
    gsap.from(meshRef.current.scale, {
      x: 0,
      y: 0,
      z: 0,
      duration: 1.5,
      ease: 'elastic.out(1, 0.5)',
    });
  }, { scope: meshRef });

  return (
    <mesh ref={meshRef}>
      <boxGeometry />
      <meshStandardMaterial color="royalblue" />
    </mesh>
  );
}
Timelines:Timelines are essential for creating robust, easily adjustable sequences of animations. Instead of relying on fragile delay properties, tweens are added to a timeline, and by default, they play one after another.28 The powerful position parameter allows for precise control over when each animation starts relative to others in the sequence.>: Starts the tween at the end of the timeline.<: Starts the tween at the beginning of the most recently added animation.+=1: Starts the tween 1 second after the end of the timeline.-=1: Starts the tween 1 second before the end of the timeline (creating an overlap).Example Timeline for the 3D Chart Reveal:JavaScriptuseGSAP(() => {
  const chartBars = //... array of mesh refs for chart bars
  const chartLine = //... ref to the chart line mesh
  const chartText = //... ref to the 3D text mesh

  const tl = gsap.timeline({ defaults: { duration: 1, ease: 'power2.out' } });

  tl.from(chartBars.map(bar => bar.current.scale), {
    y: 0,
    stagger: 0.1, // Animate each bar with a 0.1s delay
  })
 .to(chartLine.current.material, {
    opacity: 1,
  }, "<0.5") // Start this animation 0.5s after the bar animation begins
 .from(chartText.current.position, {
    y: -2,
    opacity: 0,
  }, ">-0.5"); // Start this animation 0.5s before the previous one ends
});
The choice of easing function is critical to defining the character and quality of an animation. A well-chosen ease can make an animation feel natural, energetic, or elegant.Table 1: GSAP Easing Function ComparisonEasing NameVisual CurveDescription & Use CasenoneLinearConstant speed with no acceleration. Best for mechanical or robotic movements.power1.outDeceleratingStarts fast and slows down to a stop. A natural ease for objects coming to rest.power2.inOutAccelerating & DeceleratingStarts and ends slowly, fastest in the middle. The go-to ease for smooth, professional transitions.back.out(1.7)OvershootingOvershoots the destination and then settles back. Creates a playful, bouncy, and attention-grabbing effect.elastic.out(1, 0.3)Elastic / SpringySnaps past the destination and oscillates like a rubber band before settling. Ideal for cartoonish or highly energetic effects.expo.inAcceleratingStarts very slow and accelerates rapidly. Creates a sense of dramatic build-up or high-speed launch.bounce.outBouncingSimulates an object bouncing to a stop. Used for literal bouncing effects or to add a fun, physical quality.Section 3.2: Advanced Text Animations with SplitTextStandard text animations, such as simple fades or slides, often lack the polish and impact required for a high-end user experience. GSAP's SplitText plugin is a powerful tool that elevates typography animation by deconstructing text elements into their constituent parts—lines, words, and characters—and wrapping each part in its own element, making them individually animatable.33 This enables the creation of sophisticated, visually captivating text effects.Core Concept: Granular Control Over Typographic ElementsSplitText provides the granular control needed to create complex, staggered animations. By treating each character, word, or line as an independent animation target, developers can orchestrate intricate sequences that would be impossible with traditional CSS or simpler JavaScript animations.Implementation DetailsSetup and Splitting:The SplitText plugin is a premium offering from Club GreenSock and must be registered before use, as outlined in the project setup. Once registered, it can be used to target any block-level HTML element containing text. The type property in the configuration object specifies how the text should be split.33JavaScriptimport { SplitText } from '@/lib/gsap.config'; // From centralized config
import { useGSAP } from '@gsap/react';
import { useRef } from 'react';

function AnimatedHeadline() {
  const headlineRef = useRef(null);

  useGSAP(() => {
    if (!headlineRef.current) return;

    const split = new SplitText(headlineRef.current, {
      type: "chars, words", // Split into both characters and words
      charsClass: "char",
    });

    // The split.chars property is now an array of character elements
    gsap.from(split.chars, {
      y: 100,
      opacity: 0,
      stagger: 0.05, // Each character animates 0.05s after the previous one
      duration: 1,
      ease: 'power3.out',
    });

    // Cleanup function to revert the split on component unmount
    return () => {
      split.revert();
    };
  }, { scope: headlineRef });

  return <h1 ref={headlineRef}>Alphintra Trading</h1>;
}
Staggering Animations:The true power of SplitText is unlocked when combined with GSAP's stagger property. The stagger property allows a single tween to be applied to an array of targets, with each target's animation starting slightly after the previous one. This creates beautiful, fluid, cascading effects. The stagger value can be a simple number (the delay in seconds between each start time) or an advanced object for more complex distributions (e.g., staggering from the center outwards).33 This technique is a hallmark of many award-winning websites, adding a layer of professional polish to the user interface.Part IV: Orchestrating the Scroll-Driven NarrativeThis section addresses the core of the Alphintra landing page concept: transforming a standard webpage scroll into a cinematic, narrative-driven journey through a 3D world. GSAP's ScrollTrigger plugin is the engine that powers this experience, providing a robust and performant way to link animations directly to the user's scroll position.Section 4.1: Introduction to ScrollTriggerScrollTrigger is a GSAP plugin that allows animations to be triggered by the scroll position of the page. It can be used for simple effects, like fading an element in when it enters the viewport, or for complex, scrub-linked animations where the animation's progress is directly tied to the scrollbar's position.35Core Concept: Linking Animation to Scroll PositionScrollTrigger works by creating a trigger element and defining a start and end position on the page. When the scrollbar enters this defined range, it can either play a standard time-based animation or directly control the playhead of an animation.Implementation DetailsThe ScrollTrigger is configured via an object, typically within a GSAP tween or timeline. Key properties include:trigger: The element that triggers the animation. When this element enters the viewport, the start condition is checked.36start and end: These properties define the scroll range for the animation. They are typically defined as strings with two values: the first relates to the trigger element, and the second relates to the scroller (viewport). For example, start: "top center" means the animation starts when the top of the trigger element hits the center of the viewport.35markers: true: An indispensable debugging tool that adds visual markers to the page, showing the exact start and end positions.36toggleActions: Defines the behavior for a time-based animation when the trigger enters and leaves the scroll range. It accepts four keywords: onEnter, onLeave, onEnterBack, and onLeaveBack. Common values include play, pause, resume, reset, restart, and reverse.36scrub: This is the property that enables "scrollytelling." When set to true, it links the animation's progress directly to the scroll progress within the defined range. Setting it to a number (e.g., scrub: 1) adds a smoothing effect, where the animation "catches up" to the scroll position over the specified number of seconds, creating a much smoother feel.35Section 4.2: The Cinematic Camera PathA signature technique in high-end WebGL experiences is moving the camera along a predefined path as the user scrolls, creating a "fly-through" effect.24 This transforms the user from a passive viewer into the director of their own journey through the scene.Core Concept: Mapping Scroll Progress to a 3D CurveThe technique involves creating a smooth 3D curve and then using ScrollTrigger to map the user's scroll progress to a position along that curve. A "proxy object" is often used as an intermediary. GSAP is excellent at tweening simple numeric properties on a JavaScript object, but it doesn't natively understand how to animate along a complex THREE.CatmullRomCurve3. By creating a proxy object with a progress property and animating that value from 0 to 1, we can use that reliable, scrubbed value in an onUpdate callback to perform the more complex task of positioning the camera along the curve. This pattern decouples GSAP's animation engine from Three.js's spatial mathematics, resulting in cleaner and more maintainable code.22Implementation DetailsDefine the Path: An array of THREE.Vector3 points is created to serve as the keyframes for the camera's journey. These points define the overall shape of the path.Create the Curve: The array of points is passed to a THREE.CatmullRomCurve3 constructor. This class generates a smooth, interpolated spline that passes through each of the defined points, creating a fluid path.22Animate with ScrollTrigger: A GSAP timeline is created with a ScrollTrigger configured with scrub: true. A simple tween is added to this timeline that animates a proxy object's progress property from 0 to 1 over the duration of the scroll.Update the Camera Position: In the timeline's onUpdate callback, which fires every time the animation updates, the current progress value is used to get a point on the curve via curve.getPointAt(progress). The camera's position is then set to this point on every frame.Direct the Camera's Gaze: To ensure the camera is always looking forward along the path, a second point is sampled slightly ahead on the curve (e.g., curve.getPointAt(progress + 0.01)). The camera.lookAt() method is then used to orient the camera towards this forward point, creating a natural sense of movement.22Example Implementation:JavaScriptimport * as THREE from 'three';
import { useThree } from '@react-three/fiber';
import { useGSAP } from '@gsap/react';
import { ScrollTrigger } from '@/lib/gsap.config';

function CameraPath() {
  const { camera } = useThree();

  const curve = new THREE.CatmullRomCurve3();

  useGSAP(() => {
    const timeline = gsap.timeline({
      scrollTrigger: {
        trigger: document.body,
        start: 'top top',
        end: 'bottom bottom',
        scrub: 1, // Smooth scrubbing
      },
    });

    timeline.to({}, { // Empty tween to control the timeline's progress
      onUpdate: () => {
        const progress = timeline.progress();
        const position = curve.getPointAt(progress);
        const lookAtPosition = curve.getPointAt(Math.min(progress + 0.01, 1));

        camera.position.copy(position);
        camera.lookAt(lookAtPosition);
      },
    });
  });

  return null; // This component only controls the camera
}
Section 4.3: Synchronizing Scene Animations with ScrollThe landing page should function as a cohesive narrative. As the camera moves along its path, other elements in the scene should animate in a synchronized fashion, revealing information and creating moments of visual interest that correspond to the story being told at that point in the scroll.Core Concept: A Master Timeline for a Cohesive NarrativeBy using a single, master GSAP timeline linked to the main ScrollTrigger, all major animations can be choreographed in perfect sync with the camera's movement and each other. This creates a tightly integrated and seamless user experience.Implementation DetailsUsing the Main Scroll-Linked Timeline:Animations for other 3D objects (like the trading chart reveal) can be placed directly onto the same timeline that controls the camera path proxy. The position parameter becomes crucial here. For example, an animation for the chart can be set to start when the main timeline is 30% complete ("<30%"), ensuring that the chart animates into view precisely when the camera has reached a specific viewpoint.28Independent ScrollTriggers for Ancillary Elements:For elements that are not part of the main, continuous narrative, separate ScrollTrigger instances with toggleActions can be used. For example, a piece of 3D text or a decorative element might fade in when its corresponding section of the page scrolls into view, and fade out when it leaves. This allows for more modular, self-contained animations that don't need to be tied to the global scroll progress.37 This combination of a master narrative timeline and independent, localized triggers provides both cohesive storytelling and modular control.Part V: Advanced Interactivity and UI IntegrationThis part focuses on adding layers of polish and functionality that elevate the user experience from a passive viewing to an active engagement. This includes making the 3D world feel responsive to the user's cursor and integrating a sophisticated, modern UI using the glassmorphism effect. The architectural pattern of separating the 3D scene (managed by R3F) from the 2D UI (managed by React DOM) is powerful, allowing developers to use the best tool for each job. HTML/CSS are purpose-built for creating accessible and responsive UIs, and by layering this UI on top of the Three.js canvas, the strengths of both environments can be leveraged.1Section 5.1: Mouse-Based Interactivity with RaycastingMaking the 3D world react to the user's cursor is a key technique for creating a sense of presence and interactivity. The method used to achieve this depends on the number and type of objects that need to be interactive.Core Concept: Selecting the Right Interaction Technique for the JobFor precise, object-specific interactions (like hovering over a single bar in a chart), raycasting is the appropriate tool. For broad, field-like interactions affecting thousands of elements (like a particle field), a more performant shader-based approach is necessary.Implementation DetailsRaycasting for Precise Interaction:A THREE.Raycaster is used to "pick" objects in the 3D scene. It works by casting a virtual ray from the camera's position through the cursor's position on the screen and into the 3D scene. It can then report which objects the ray intersects.40The process is as follows:Listen for the mousemove event.On each event, update a THREE.Vector2 with the mouse coordinates, normalized to a range of -1 to +1.Update the raycaster using raycaster.setFromCamera(mouse, camera).Call raycaster.intersectObjects(scene.children) to get an array of intersected objects.If an intersection is found, a GSAP animation can be triggered to highlight the object (e.g., change its material color, emissive property, or scale it up slightly).40Shader Uniforms for Mass Interaction:Performing raycasting against thousands of particles on every mouse movement would be prohibitively expensive and would cause significant performance degradation. A much more efficient method is to pass the mouse's 2D coordinates directly to the particle shader as a uniform vec2 uMouse. Inside the vertex shader, for each particle, the distance between the particle's position and the mouse's position can be calculated. This distance value can then be used to create a repulsion effect (by displacing the particle's position away from the mouse) or a highlighting effect (by increasing the particle's size or brightness), all performed in parallel on the GPU.16Section 5.2: Implementing the Glassmorphism UIGlassmorphism is a UI design trend that creates a "frosted glass" effect, where UI elements are semi-transparent and appear to blur the content behind them. This effect adds depth and a modern aesthetic to the interface.Core Concept: Layering HTML on a Transparent WebGL CanvasThe effect is achieved by layering standard HTML UI elements on top of the Three.js canvas. The key is to make the canvas background transparent and then apply the CSS backdrop-filter property to the overlying UI elements.Implementation DetailsHTML Structure: In the React component tree, the <Canvas> component and the HTML UI components should be siblings. CSS positioning will be used to stack them.CSS Positioning: A container div wraps both the canvas and the UI. The canvas is given position: absolute, top: 0, left: 0, and a lower z-index (e.g., z-index: 1). The UI container is also given position: absolute and a higher z-index (e.g., z-index: 2) to ensure it sits on top.Three.js Renderer Transparency: This is a critical step. The R3F <Canvas> component must be initialized with the gl={{ alpha: true }} prop. This tells the WebGLRenderer to create a drawing buffer with an alpha channel, making its background transparent. Without this, the canvas will have an opaque background, and the backdrop-filter will have nothing to blur.9Glassmorphism CSS: The following CSS properties are applied to the UI elements that should have the frosted glass effect:background-color: rgba(255, 255, 255, 0.1);: A semi-transparent background color provides the "tint" of the glass.backdrop-filter: blur(10px);: This is the essential property. It applies a Gaussian blur to whatever content is rendered behind the element in the stacking context.44border: 1px solid rgba(255, 255, 255, 0.2);: A subtle, semi-transparent border helps to define the edges of the glass panel, enhancing the effect.border-radius: 12px;: Rounded corners are characteristic of the glassmorphism style.Example CSS for a Glassmorphism Card:CSS.glass-card {
  position: relative;
  padding: 2rem;
  border-radius: 12px;
  
  /* Glass effect */
  background-color: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px); /* For Safari */
  
  /* Edge highlight */
  border: 1px solid rgba(255, 255, 255, 0.2);
  
  /* Optional shadow for depth */
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
}
This combination of techniques allows for a seamless integration of a fully interactive 3D background with a modern, functional, and aesthetically pleasing 2D user interface.Part VI: Performance Engineering for a Flawless ExperiencePerformance optimization is not a final step in the development process but a continuous consideration that should inform every architectural and implementation decision. A visually stunning and interactive experience is rendered ineffective if it is sluggish, unresponsive, or inaccessible on a user's device. This final section covers the critical strategies and tools required to ensure the complex Alphintra landing page runs smoothly across a wide range of hardware. The goal is to navigate the inherent trade-off between visual fidelity and performance, making intelligent choices to deliver the best possible experience.47Section 6.1: Three.js Optimization Deep DiveMaintaining a consistently high frame rate (ideally 60 FPS) in a complex WebGL scene requires a deep understanding of what causes performance bottlenecks on the GPU and CPU.Core Concept: Minimizing Work for the GPU and CPUThe fundamental principles of Three.js optimization revolve around reducing the number of instructions sent to the GPU (draw calls), simplifying the calculations the GPU has to perform (geometry and shaders), and minimizing the amount of data that needs to be transferred (textures).Implementation DetailsDraw Calls:A draw call is a command from the CPU to the GPU to render a group of triangles. Each draw call has a certain amount of overhead, so minimizing them is one of the most effective optimizations.Geometry Merging: For static objects that share the same material, their geometries can be merged into a single BufferGeometry using BufferGeometryUtils.mergeBufferGeometries. This allows them to be rendered in a single draw call.10Instancing: As covered previously, InstancedMesh is the preferred method for rendering a large number of objects that share the same geometry and material but have different positions, rotations, or scales.19Geometry and Textures:Polygon Count: Use low-polygon models wherever possible. The fewer vertices and faces the GPU has to process, the faster the scene will render.11Texture Dimensions: Keep texture dimensions to powers of two (e.g., 512x512, 1024x1024, 2048x2048). This allows the GPU to generate mipmaps and handle memory more efficiently. Avoid textures larger than 2048x2048 for web use, as they can cause issues on mobile devices.10 Use compressed texture formats like KTX2 or Basis where supported to dramatically reduce GPU memory usage.25Lights and Shadows:Cost of Lights: Real-time lights, especially those that cast shadows, are computationally expensive. Use as few as necessary.10Shadow Maps: Real-time shadows require an extra render pass for each light, making them a major performance bottleneck. For static scenes, shadows should be baked into textures. For dynamic scenes, use the smallest possible shadow map resolution (shadow-mapSize) that still looks acceptable and keep the shadow camera's frustum as tight as possible to maximize the use of that resolution.10 Drei's <ContactShadows> can provide a cheap, plausible alternative to real-time shadows for objects on a ground plane.Culling and Level of Detail (LOD):Frustum Culling: Three.js automatically performs frustum culling, which means it doesn't render objects that are outside the camera's viewing frustum. This is a built-in optimization.49Level of Detail (LOD): For large scenes, THREE.LOD can be used to manage complexity. This object allows for displaying different versions of a model (from high-poly to low-poly) based on its distance from the camera, reducing the geometric load for distant objects.10Section 6.2: GSAP Performance Best PracticesEfficient GSAP code is crucial for ensuring that animations, especially those tied to scroll events, are smooth and do not cause "jank" or stuttering.Core Concept: Clean Code and Efficient Property AnimationGSAP performance best practices focus on proper cleanup within component lifecycles, animating properties that are cheap for the browser to render, and providing hints to the browser to optimize rendering.Implementation DetailsAnimation Cleanup:In a React environment, failing to clean up animations is a common source of memory leaks and performance degradation. The useGSAP hook simplifies this. The function returned from the useGSAP effect is the cleanup function. It should use context.revert() to safely revert all animations and ScrollTriggers created within its scope to their initial states, making them ready for garbage collection.4Animating Performant Properties:When animating DOM elements, always prioritize animating CSS transform (via GSAP's x, y, scale, rotation shortcuts) and opacity. These properties can be handled by the browser's compositor thread and are GPU-accelerated, meaning they don't trigger expensive layout recalculations or repaints of the entire page. Avoid animating layout-affecting properties like width, height, margin, or top/left whenever possible.30The will-change Property:For elements undergoing complex or persistent transform animations, applying the CSS property will-change: transform; can provide a performance boost. This property acts as a hint to the browser that the element is likely to be animated, allowing the browser to move it to its own compositor layer in advance. This can prevent visual tearing and stuttering, but it should be used judiciously as it consumes extra memory.30Section 6.3: Monitoring and DebuggingEffective optimization is impossible without accurate measurement. A suite of monitoring and debugging tools is essential for identifying performance bottlenecks and verifying the impact of optimizations.Core Concept: Real-Time and In-Depth Performance AnalysisThe toolkit for performance analysis includes simple, real-time on-screen displays for quick checks and more powerful browser-integrated tools for deep-dive analysis of CPU, GPU, and WebGL-specific activity.Implementation Detailsstats.js and R3F <Stats>:For a quick, real-time overview of performance, the stats.js library is invaluable. In a React Three Fiber project, Drei's <Stats> component provides an easy way to add this to the scene. It displays a simple on-screen panel showing the current frames per second (FPS), memory usage, and, crucially, the number of draw calls per frame.19Browser Developer Tools:The "Performance" tab in Chrome DevTools is a powerful tool for profiling. It can record a short period of interaction and provide a detailed "flame graph" that shows exactly what functions are being called on the main thread and how much time they are taking. This is essential for identifying CPU-bound bottlenecks, such as long-running JavaScript functions in the render loop.19Spector.js:For deep-diving into WebGL-specific issues, the Spector.js browser extension is the industry-standard tool. It allows a developer to capture a single frame of the WebGL render. It then provides a complete, step-by-step breakdown of every command sent to the GPU for that frame, including every draw call, the associated geometry, textures, and the exact vertex and fragment shaders used. This level of detail is indispensable for debugging complex rendering issues and optimizing shaders.19Table 2: Performance Optimization ChecklistCategoryChecklist ItemPriorityImpactRenderingIs the Device Pixel Ratio (DPR) capped at a reasonable value (e.g., 2)?HighReduces the number of pixels rendered, significantly improving GPU performance on high-res screens.Is the renderer's background set to transparent (alpha: true) only if necessary?MediumAvoids unnecessary alpha compositing, which can have a minor performance cost.Is the render loop paused (frameloop="demand") when the scene is static?HighDrastically reduces CPU/GPU usage and battery consumption when no animation is occurring.GeometryAre static meshes with the same material merged to reduce draw calls?HighReduces CPU overhead by minimizing the number of commands sent to the GPU.Are InstancedMesh used for large numbers of repeating objects?HighThe most effective way to render thousands of similar objects with minimal draw calls.Are low-polygon models used, especially for distant or complex objects?HighReduces the number of vertices the GPU must process per frame.TexturesAre texture dimensions powers of two (e.g., 1024x1024)?HighEnables mipmapping and more efficient memory handling by the GPU.Are textures compressed (e.g., KTX2, Basis, or simple PNG/JPG optimization)?HighReduces GPU memory usage and initial download time.Lighting/ShadowsAre real-time shadows used sparingly? Have shadows been baked for static objects?HighReal-time shadows are one of the most expensive rendering features.Is the shadow map resolution (shadow-mapSize) as low as possible?MediumReduces the memory and processing cost of generating shadow maps.Is an <Environment> map used for realistic lighting instead of many point lights?HighProvides high-quality, nuanced lighting with significantly better performance than multiple dynamic lights.GSAPAre all animations and ScrollTriggers properly cleaned up using context.revert()?CriticalPrevents memory leaks and cascading performance issues in single-page applications.Are animations primarily targeting transform and opacity?HighLeverages GPU acceleration and avoids costly browser layout recalculations.Is scrub smoothing used on ScrollTriggers to avoid jitter from low-resolution scroll events?MediumImproves the perceived smoothness of scroll-linked animations.ConclusionsThe development of a high-end, interactive landing page like the one envisioned for Alphintra is a multidisciplinary endeavor, blending creative design, 3D artistry, and sophisticated front-end engineering. The successful integration of Three.js and GSAP is not merely about using two powerful libraries in tandem; it is about adopting an architectural philosophy that leverages the strengths of each within a modern, component-based framework.The analysis leads to several key actionable recommendations:Adopt a React Three Fiber (R3F) Architecture: The declarative, component-based nature of R3F is the most robust and scalable approach for building complex, state-driven 3D experiences. It simplifies scene management, promotes code reusability, and integrates seamlessly with React's ecosystem, including GSAP's useGSAP hook for lifecycle-aware animation management. This foundation is critical for the project's long-term maintainability.Prioritize a Narrative-Driven Scroll Experience: The core of the user engagement strategy should be the scroll-driven camera path. By using a CatmullRomCurve3 animated via a scrubbed GSAP ScrollTrigger, the user is transformed from a passive observer to an active participant in a visual narrative. This technique, combined with synchronized animations of scene elements on a master timeline, creates a cohesive and memorable journey.Implement a Hybrid UI/WebGL Approach: The most effective and pragmatic method for building the user interface is to layer standard HTML/CSS elements on top of the Three.js canvas. This allows for the creation of an accessible, responsive, and feature-rich UI using familiar web technologies, while leveraging WebGL for the immersive visual background. The glassmorphism effect, achieved with backdrop-filter on a transparent canvas, serves as the aesthetic bridge between these two layers.Make Performance a Day-One Priority: Performance optimization cannot be an afterthought. It must be integrated into every stage of the workflow, from 3D asset creation (low-poly modeling, texture baking, Draco compression) to development (minimizing draw calls via instancing and merging, using GPU-accelerated shaders) and animation (animating performant properties, ensuring proper cleanup). Continuous monitoring with tools like stats.js and browser dev tools is essential to maintain a smooth experience across all target devices.By adhering to these principles—a strong R3F architecture, a compelling scroll-driven narrative, a practical hybrid UI, and a relentless focus on performance—the Alphintra landing page can achieve its goal of becoming a benchmark for immersive and effective digital experiences in the financial technology sector.
