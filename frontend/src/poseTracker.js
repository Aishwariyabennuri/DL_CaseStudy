import {
  PoseLandmarker,
  FilesetResolver
} from "@mediapipe/tasks-vision";

let poseLandmarker = null;

export async function initializePoseTracker() {
  const vision = await FilesetResolver.forVisionTasks(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
  );

  poseLandmarker = await PoseLandmarker.createFromOptions(
    vision,
    {
      baseOptions: {
        modelAssetPath:
          "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
        delegate: "GPU"
      },
      runningMode: "VIDEO",
      numPoses: 1
    }
  );

  return poseLandmarker;
}

export function detectPose(video) {
  if (!poseLandmarker || video.readyState < 2) {
    return null;
  }

  return poseLandmarker.detectForVideo(video, performance.now());
}