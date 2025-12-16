/**
 * Testing Panel Component
 * Allows testing face detection and recognition without active sessions
 * Shows detailed debugging information
 */
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/apiConfig';

interface DetectionInfo {
  faces_detected: number;
  detection_time_ms: number;
  faces: Array<{
    x: number;
    y: number;
    width: number;
    height: number;
  }>;
  warning?: string;
}

interface EmbeddingInfo {
  extraction_time_ms: number;
  embedding_shape: number | number[];
}

interface MatchingResult {
  student_id: string;
  student_name: string;
  similarities: number[];
  distances: number[];
  best_similarity: number;
  avg_similarity: number;
  best_distance: number | null;
  embedding_count: number;
}

interface MatchingInfo {
  total_students_tested: number;
  matching_time_ms: number;
  results: MatchingResult[];
  best_match: MatchingResult | null;
}

interface RecognitionResult {
  recognized: boolean;
  student_id: string | null;
  student_name: string | null;
  confidence: number;
  threshold_used: number;
}

interface TestResponse {
  success: boolean;
  message: string;
  recognition?: RecognitionResult;
  detection: DetectionInfo;
  embedding: EmbeddingInfo;
  matching: MatchingInfo;
}

const TestingPanel: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState('Click "Start Camera" to begin testing');
  const [testResults, setTestResults] = useState<TestResponse | null>(null);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsCameraActive(true);
        setMessage('Camera ready. Capture an image to test detection or recognition.');
      }
    } catch (error) {
      console.error('Error accessing webcam:', error);
      setMessage('Failed to access webcam. Please allow permissions and try again.');
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      setIsCameraActive(false);
      setMessage('Camera stopped');
    }
  };

  const captureFrame = (): string | null => {
    if (!videoRef.current || !canvasRef.current) return null;

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const context = canvas.getContext('2d');

    if (!context) return null;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL('image/jpeg', 0.8);
  };

  const testDetection = async () => {
    const frameData = captureFrame();
    if (!frameData) {
      setMessage('Failed to capture frame');
      return;
    }

    setIsProcessing(true);
    setMessage('Testing face detection...');

    try {
      const response = await axios.post(`${API_BASE_URL}/test-recognition`, {
        image: frameData
      });

      const result: TestResponse = response.data;
      setTestResults(result);

      if (result.success) {
        setMessage(`Detection test completed. Found ${result.detection.faces_detected} face(s).`);
      } else {
        setMessage(result.message);
      }
    } catch (error: any) {
      console.error('Detection test error:', error);
      const reason = error.response?.data?.error || error.message || 'Network error';
      setMessage(`Detection test failed: ${reason}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const testRecognition = async () => {
    const frameData = captureFrame();
    if (!frameData) {
      setMessage('Failed to capture frame');
      return;
    }

    setIsProcessing(true);
    setMessage('Testing face recognition...');

    try {
      const response = await axios.post(`${API_BASE_URL}/test-recognition`, {
        image: frameData
      });

      const result: TestResponse = response.data;
      setTestResults(result);

      if (result.success) {
        if (result.recognition && result.recognition.recognized) {
          setMessage(`Recognition successful: ${result.recognition.student_name} (${(result.recognition.confidence * 100).toFixed(1)}%)`);
        } else {
          setMessage('Face detected but not recognized. Check matching results below.');
        }
      } else {
        setMessage(result.message);
      }
    } catch (error: any) {
      console.error('Recognition test error:', error);
      const reason = error.response?.data?.error || error.message || 'Network error';
      setMessage(`Recognition test failed: ${reason}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Face Detection & Recognition Testing</h1>
        <div className="flex gap-2">
          {!isCameraActive ? (
            <button
              onClick={startCamera}
              className="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Start Camera
            </button>
          ) : (
            <button
              onClick={stopCamera}
              className="px-6 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Stop Camera
            </button>
          )}
        </div>
      </div>

      {/* Status Message */}
      <div className={`mb-6 p-4 rounded-lg ${isProcessing ? 'bg-yellow-100 border border-yellow-300' : 'bg-gray-100 border border-gray-300'}`}>
        <p className="text-sm">{message}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Video Feed */}
        <div className="space-y-4">
          <div className={`relative rounded-lg overflow-hidden border-4 ${isCameraActive ? 'border-green-500' : 'border-gray-300'}`}>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-auto bg-black"
            />
            <canvas ref={canvasRef} className="hidden" />

            {/* Camera Status Overlay */}
            <div className={`absolute top-4 right-4 px-4 py-2 rounded-full font-semibold ${isCameraActive ? 'bg-green-500 text-white' : 'bg-gray-500 text-white'}`}>
              {isCameraActive ? 'ACTIVE' : 'INACTIVE'}
            </div>
          </div>

          {/* Test Buttons */}
          <div className="flex gap-2">
            <button
              onClick={testDetection}
              disabled={!isCameraActive || isProcessing}
              className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Test Detection
            </button>
            <button
              onClick={testRecognition}
              disabled={!isCameraActive || isProcessing}
              className="flex-1 px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Test Recognition
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div className="space-y-4">
          {testResults && (
            <>
              {/* Recognition Result */}
              {testResults.recognition && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-3">Recognition Result</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Recognized:</span>
                      <span className={`font-medium ${testResults.recognition.recognized ? 'text-green-600' : 'text-red-600'}`}>
                        {testResults.recognition.recognized ? 'YES' : 'NO'}
                      </span>
                    </div>
                    {testResults.recognition.student_name && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Student:</span>
                          <span className="font-medium">{testResults.recognition.student_name}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Confidence:</span>
                          <span className="font-medium">{(testResults.recognition.confidence * 100).toFixed(1)}%</span>
                        </div>
                      </>
                    )}
                    <div className="flex justify-between">
                      <span className="text-gray-600">Threshold:</span>
                      <span className="font-medium">{(testResults.recognition.threshold_used * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Detection Info */}
              {testResults.detection ? (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-3">Detection Info</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Faces Detected:</span>
                      <span className="font-medium">{testResults.detection.faces_detected}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Detection Time:</span>
                      <span className="font-medium">{testResults.detection.detection_time_ms.toFixed(2)}ms</span>
                    </div>
                    {testResults.detection.faces.length > 0 && (
                      <div>
                        <span className="text-gray-600">Face Locations:</span>
                        <div className="mt-1 space-y-1">
                          {testResults.detection.faces.map((face, idx) => (
                            <div key={idx} className="text-sm bg-gray-50 p-2 rounded">
                              Face {idx + 1}: x={face.x}, y={face.y}, {face.width}x{face.height}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {testResults.detection.warning && (
                      <div className="text-orange-600 text-sm bg-orange-50 p-2 rounded">
                        ⚠️ {testResults.detection.warning}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="bg-yellow-50 rounded-lg shadow p-6 border border-yellow-200">
                  <h3 className="text-lg font-semibold mb-3 text-yellow-800">Detection Info</h3>
                  <p className="text-yellow-700">No detection information available.</p>
                </div>
              )}

              {/* Embedding Info */}
              {testResults.embedding ? (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-3">Embedding Info</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Extraction Time:</span>
                      <span className="font-medium">{testResults.embedding.extraction_time_ms.toFixed(2)}ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Embedding Shape:</span>
                      <span className="font-medium">
                        {Array.isArray(testResults.embedding.embedding_shape)
                          ? testResults.embedding.embedding_shape.join('x')
                          : testResults.embedding.embedding_shape}
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-yellow-50 rounded-lg shadow p-6 border border-yellow-200">
                  <h3 className="text-lg font-semibold mb-3 text-yellow-800">Embedding Info</h3>
                  <p className="text-yellow-700">No embedding information available.</p>
                </div>
              )}

              {/* Matching Results */}
              {testResults.matching ? (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-3">Matching Results</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Students Tested:</span>
                      <span className="font-medium">{testResults.matching.total_students_tested}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Matching Time:</span>
                      <span className="font-medium">{testResults.matching.matching_time_ms.toFixed(2)}ms</span>
                    </div>
                    <div className="mt-4">
                      <h4 className="font-medium mb-2">Top Matches:</h4>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {testResults.matching.results.slice(0, 5).map((result, idx) => (
                          <div key={result.student_id} className={`p-3 rounded border ${idx === 0 ? 'border-green-300 bg-green-50' : 'border-gray-200'}`}>
                            <div className="flex justify-between items-center">
                              <span className="font-medium">{result.student_name}</span>
                              <span className={`text-sm px-2 py-1 rounded ${result.best_similarity >= (testResults.recognition?.threshold_used || 0.5) ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                {(result.best_similarity * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="text-xs text-gray-600 mt-1">
                              Distance: {result.best_distance?.toFixed(4) || 'N/A'} | Embeddings: {result.embedding_count}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-yellow-50 rounded-lg shadow p-6 border border-yellow-200">
                  <h3 className="text-lg font-semibold mb-3 text-yellow-800">Matching Results</h3>
                  <p className="text-yellow-700">No matching results available. Detection may have failed or no students are enrolled in the system.</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default TestingPanel;