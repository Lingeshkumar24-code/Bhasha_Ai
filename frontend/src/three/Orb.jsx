import { useEffect, useRef } from 'react';
import * as THREE from 'three';

/**
 * Interactive 3D orb built with plain three.js (kept dependency-light so
 * the Render free-tier static build stays fast — see spec section 8).
 * Reacts to: mouse movement, mic volume, and pipeline state
 * (idle / listening / processing / speaking).
 */
export default function Orb({ state = 'idle', volume = 0, size = 320 }) {
  const mountRef = useRef(null);
  const stateRef = useRef(state);
  const volumeRef = useRef(volume);

  useEffect(() => { stateRef.current = state; }, [state]);
  useEffect(() => { volumeRef.current = volume; }, [volume]);

  useEffect(() => {
    const mount = mountRef.current;
    const isLowEnd = navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4;
    const detail = isLowEnd ? 24 : 64;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.z = 4.2;

    const renderer = new THREE.WebGLRenderer({ antialias: !isLowEnd, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, isLowEnd ? 1 : 2));
    renderer.setSize(size, size);
    mount.appendChild(renderer.domElement);

    const geometry = new THREE.IcosahedronGeometry(1.3, detail > 32 ? 4 : 2);
    const material = new THREE.MeshStandardMaterial({
      color: 0xffd700, emissive: 0xfb8500, emissiveIntensity: 0.6,
      wireframe: true, roughness: 0.2, metalness: 0.5,
    });
    const orb = new THREE.Mesh(geometry, material);
    scene.add(orb);

    const coreGeo = new THREE.SphereGeometry(0.85, detail > 32 ? 48 : 20, detail > 32 ? 48 : 20);
    const coreMat = new THREE.MeshBasicMaterial({ color: 0xffb703, transparent: true, opacity: 0.3 });
    const core = new THREE.Mesh(coreGeo, coreMat);
    scene.add(core);

    scene.add(new THREE.AmbientLight(0xffdca0, 0.6));
    const point = new THREE.PointLight(0xffd700, 2, 10);
    point.position.set(2, 2, 2);
    scene.add(point);

    let targetX = 0, targetY = 0;
    const onMouseMove = (e) => {
      const rect = mount.getBoundingClientRect();
      targetX = ((e.clientX - rect.left) / rect.width - 0.5) * 0.6;
      targetY = ((e.clientY - rect.top) / rect.height - 0.5) * 0.6;
    };
    window.addEventListener('mousemove', onMouseMove);

    let frameId;
    const clock = new THREE.Clock();
    const animate = () => {
      const t = clock.getElapsedTime();
      const s = stateRef.current;
      const vol = volumeRef.current;

      let pulse = 1;
      const colorTargets = {
        idle: 0xffd700, listening: 0xffd700, processing: 0xfb8500, speaking: 0xffb703,
      };

      if (s === 'listening') pulse = 1 + vol * 0.4 + Math.sin(t * 4) * 0.02;
      else if (s === 'processing') pulse = 1 + Math.sin(t * 6) * 0.06;
      else if (s === 'speaking') pulse = 1 + Math.sin(t * 10) * 0.08;
      else pulse = 1 + Math.sin(t * 0.8) * 0.02;

      orb.scale.setScalar(pulse);
      core.scale.setScalar(pulse * 0.9);
      orb.rotation.y += s === 'processing' ? 0.02 : 0.004;
      orb.rotation.x += 0.0015;

      orb.rotation.y += (targetX - 0) * 0.01;
      orb.rotation.x += (targetY - 0) * 0.01;

      material.color.lerp(new THREE.Color(colorTargets[s] || 0xffd700), 0.05);

      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('mousemove', onMouseMove);
      renderer.dispose();
      geometry.dispose();
      material.dispose();
      coreGeo.dispose();
      coreMat.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, [size]);

  return <div ref={mountRef} style={{ width: size, height: size, margin: '0 auto' }} />;
}
