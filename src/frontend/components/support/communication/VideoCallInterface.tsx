'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { 
  Video, 
  VideoOff, 
  Mic, 
  MicOff, 
  Phone, 
  PhoneOff, 
  Monitor, 
  Settings,
  MessageSquare,
  Users,
  Maximize2,
  Minimize2,
  Volume2,
  VolumeX
} from 'lucide-react';
import { 
  customerSupportApi, 
  CreateCommunicationRequest,
  CommunicationType
} from '@/lib/api/customer-support-api';
import { toast } from 'react-hot-toast';

interface VideoCallInterfaceProps {
  ticketId: string;
  isAgent: boolean;
  agentName?: string;
  userName?: string;
  onCallEnd: () => void;
  isOpen: boolean;
  onClose: () => void;
}

interface CallParticipant {
  id: string;
  name: string;
  isLocal: boolean;
  videoEnabled: boolean;
  audioEnabled: boolean;
  isScreenSharing: boolean;
}

export default function VideoCallInterface({
  ticketId,
  isAgent,
  agentName,
  userName,
  onCallEnd,
  isOpen,
  onClose
}: VideoCallInterfaceProps) {
  const [isCallActive, setIsCallActive] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [callDuration, setCallDuration] = useState(0);
  const [participants, setParticipants] = useState<CallParticipant[]>([]);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [isFullscreen, setIsFullscreen] = useState(false);

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const screenShareRef = useRef<HTMLVideoElement>(null);
  const callStartTimeRef = useRef<number | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isCallActive && callStartTimeRef.current) {
      durationIntervalRef.current = setInterval(() => {
        const elapsed = Math.floor((Date.now() - callStartTimeRef.current!) / 1000);
        setCallDuration(elapsed);
      }, 1000);
    } else {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    }

    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [isCallActive]);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startCall = async () => {
    setIsConnecting(true);
    setConnectionStatus('connecting');
    
    try {
      // Request camera and microphone permissions
      const stream = await navigator.mediaDevices.getUserMedia({
        video: isVideoEnabled,
        audio: isAudioEnabled
      });

      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // Initialize local participant
      const localParticipant: CallParticipant = {
        id: 'local',
        name: isAgent ? (agentName || 'Agent') : (userName || 'User'),
        isLocal: true,
        videoEnabled: isVideoEnabled,
        audioEnabled: isAudioEnabled,
        isScreenSharing: false
      };

      setParticipants([localParticipant]);
      setIsCallActive(true);
      setConnectionStatus('connected');
      callStartTimeRef.current = Date.now();

      // Log call start in communications
      await logCallEvent('started');

      // Simulate remote participant joining after 2 seconds
      setTimeout(() => {
        const remoteParticipant: CallParticipant = {
          id: 'remote',
          name: isAgent ? (userName || 'Customer') : (agentName || 'Support Agent'),
          isLocal: false,
          videoEnabled: true,
          audioEnabled: true,
          isScreenSharing: false
        };
        setParticipants(prev => [...prev, remoteParticipant]);
      }, 2000);

      toast.success('Call started successfully');
    } catch (error) {
      console.error('Failed to start call:', error);
      toast.error('Failed to access camera/microphone');
      setConnectionStatus('disconnected');
    } finally {
      setIsConnecting(false);
    }
  };

  const endCall = async () => {
    setIsCallActive(false);
    setConnectionStatus('disconnected');
    setParticipants([]);
    callStartTimeRef.current = null;
    setCallDuration(0);

    // Stop all media streams
    if (localVideoRef.current?.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      localVideoRef.current.srcObject = null;
    }

    // Log call end
    await logCallEvent('ended', callDuration);
    
    toast.success('Call ended');
    onCallEnd();
  };

  const toggleVideo = async () => {
    if (localVideoRef.current?.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream;
      const videoTrack = stream.getVideoTracks()[0];
      
      if (videoTrack) {
        videoTrack.enabled = !isVideoEnabled;
        setIsVideoEnabled(!isVideoEnabled);
        
        // Update local participant
        setParticipants(prev => prev.map(p => 
          p.isLocal ? { ...p, videoEnabled: !isVideoEnabled } : p
        ));
      }
    }
  };

  const toggleAudio = () => {
    if (localVideoRef.current?.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream;
      const audioTrack = stream.getAudioTracks()[0];
      
      if (audioTrack) {
        audioTrack.enabled = !isAudioEnabled;
        setIsAudioEnabled(!isAudioEnabled);
        
        // Update local participant
        setParticipants(prev => prev.map(p => 
          p.isLocal ? { ...p, audioEnabled: !isAudioEnabled } : p
        ));
      }
    }
  };

  const startScreenShare = async () => {
    try {
      const screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true
      });

      if (screenShareRef.current) {
        screenShareRef.current.srcObject = screenStream;
      }

      setIsScreenSharing(true);
      
      // Update local participant
      setParticipants(prev => prev.map(p => 
        p.isLocal ? { ...p, isScreenSharing: true } : p
      ));

      // Handle screen share end
      screenStream.getVideoTracks()[0].onended = () => {
        stopScreenShare();
      };

      await logCallEvent('screen_share_started');
      toast.success('Screen sharing started');
    } catch (error) {
      console.error('Failed to start screen share:', error);
      toast.error('Failed to start screen sharing');
    }
  };

  const stopScreenShare = () => {
    if (screenShareRef.current?.srcObject) {
      const stream = screenShareRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      screenShareRef.current.srcObject = null;
    }

    setIsScreenSharing(false);
    
    // Update local participant
    setParticipants(prev => prev.map(p => 
      p.isLocal ? { ...p, isScreenSharing: false } : p
    ));

    logCallEvent('screen_share_ended');
  };

  const logCallEvent = async (event: string, duration?: number) => {
    try {
      const content = duration 
        ? `Video call ${event} (Duration: ${formatDuration(duration)})`
        : `Video call ${event}`;

      const request: CreateCommunicationRequest = {
        content,
        communicationType: CommunicationType.VIDEO_CALL,
        isInternal: false
      };

      await customerSupportApi.addCommunication(ticketId, request);
    } catch (error) {
      console.error('Failed to log call event:', error);
    }
  };

  const ParticipantVideo = ({ participant }: { participant: CallParticipant }) => (
    <div className="relative bg-gray-900 rounded-lg overflow-hidden">
      <video
        ref={participant.isLocal ? localVideoRef : remoteVideoRef}
        autoPlay
        muted={participant.isLocal}
        playsInline
        className="w-full h-full object-cover"
      />
      
      {!participant.videoEnabled && (
        <div className="absolute inset-0 bg-gray-800 flex items-center justify-center">
          <div className="text-center text-white">
            <div className="w-16 h-16 bg-gray-600 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-xl font-bold">
                {participant.name.charAt(0).toUpperCase()}
              </span>
            </div>
            <p className="text-sm">{participant.name}</p>
          </div>
        </div>
      )}
      
      <div className="absolute bottom-2 left-2 flex items-center gap-2">
        <Badge variant={participant.audioEnabled ? "default" : "destructive"} className="text-xs">
          {participant.audioEnabled ? <Mic className="w-3 h-3" /> : <MicOff className="w-3 h-3" />}
        </Badge>
        <Badge variant={participant.videoEnabled ? "default" : "secondary"} className="text-xs">
          {participant.videoEnabled ? <Video className="w-3 h-3" /> : <VideoOff className="w-3 h-3" />}
        </Badge>
        {participant.isScreenSharing && (
          <Badge variant="outline" className="text-xs">
            <Monitor className="w-3 h-3" />
          </Badge>
        )}
      </div>
      
      <div className="absolute bottom-2 right-2">
        <Badge variant="outline" className="text-xs">
          {participant.name}
        </Badge>
      </div>
    </div>
  );

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className={`max-w-4xl ${isFullscreen ? 'w-screen h-screen max-w-none' : 'max-h-[90vh]'}`}>
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Video className="w-5 h-5" />
              Video Call - Ticket #{ticketId}
              {isCallActive && (
                <Badge variant="outline">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></div>
                  {formatDuration(callDuration)}
                </Badge>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsFullscreen(!isFullscreen)}
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </Button>
              
              <Badge variant={connectionStatus === 'connected' ? 'default' : 'destructive'}>
                {connectionStatus}
              </Badge>
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {!isCallActive ? (
            /* Pre-call Setup */
            <div className="text-center py-8">
              <div className="space-y-4">
                <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto">
                  <Video className="w-8 h-8 text-white" />
                </div>
                
                <div>
                  <h3 className="text-lg font-medium">Ready to start video call?</h3>
                  <p className="text-gray-600">
                    Connect with {isAgent ? 'the customer' : 'support agent'} via video call
                  </p>
                </div>

                <div className="flex items-center justify-center gap-4">
                  <Button
                    variant="outline"
                    onClick={toggleVideo}
                    className={!isVideoEnabled ? 'bg-red-50 border-red-200' : ''}
                  >
                    {isVideoEnabled ? <Video className="w-4 h-4 mr-2" /> : <VideoOff className="w-4 h-4 mr-2" />}
                    {isVideoEnabled ? 'Video On' : 'Video Off'}
                  </Button>
                  
                  <Button
                    variant="outline"
                    onClick={toggleAudio}
                    className={!isAudioEnabled ? 'bg-red-50 border-red-200' : ''}
                  >
                    {isAudioEnabled ? <Mic className="w-4 h-4 mr-2" /> : <MicOff className="w-4 h-4 mr-2" />}
                    {isAudioEnabled ? 'Mic On' : 'Mic Off'}
                  </Button>
                </div>

                <Button 
                  onClick={startCall} 
                  disabled={isConnecting}
                  size="lg"
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Phone className="w-5 h-5 mr-2" />
                  {isConnecting ? 'Connecting...' : 'Start Call'}
                </Button>
              </div>
            </div>
          ) : (
            /* Active Call Interface */
            <div className="space-y-4">
              {/* Main Video Area */}
              <div className="relative">
                {isScreenSharing ? (
                  /* Screen Share View */
                  <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden">
                    <video
                      ref={screenShareRef}
                      autoPlay
                      playsInline
                      className="w-full h-full object-contain"
                    />
                  </div>
                ) : (
                  /* Regular Video Grid */
                  <div className={`grid gap-4 ${participants.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}`}>
                    {participants.map(participant => (
                      <div key={participant.id} className="aspect-video">
                        <ParticipantVideo participant={participant} />
                      </div>
                    ))}
                  </div>
                )}

                {/* Picture-in-Picture for screen share */}
                {isScreenSharing && (
                  <div className="absolute bottom-4 right-4 w-48 aspect-video">
                    {participants.find(p => p.isLocal) && (
                      <ParticipantVideo participant={participants.find(p => p.isLocal)!} />
                    )}
                  </div>
                )}
              </div>

              {/* Call Controls */}
              <div className="flex items-center justify-center gap-4 p-4 bg-gray-50 rounded-lg">
                <Button
                  variant={isAudioEnabled ? "outline" : "destructive"}
                  size="sm"
                  onClick={toggleAudio}
                >
                  {isAudioEnabled ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
                </Button>

                <Button
                  variant={isVideoEnabled ? "outline" : "destructive"}
                  size="sm"
                  onClick={toggleVideo}
                >
                  {isVideoEnabled ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
                </Button>

                <Button
                  variant={isScreenSharing ? "default" : "outline"}
                  size="sm"
                  onClick={isScreenSharing ? stopScreenShare : startScreenShare}
                >
                  <Monitor className="w-4 h-4" />
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsMuted(!isMuted)}
                >
                  {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                </Button>

                <Button variant="outline" size="sm">
                  <MessageSquare className="w-4 h-4" />
                </Button>

                <Button variant="outline" size="sm">
                  <Settings className="w-4 h-4" />
                </Button>

                <Button
                  variant="destructive"
                  size="sm"
                  onClick={endCall}
                >
                  <PhoneOff className="w-4 h-4" />
                </Button>
              </div>

              {/* Call Info */}
              <div className="flex items-center justify-between text-sm text-gray-600 px-4">
                <div className="flex items-center gap-4">
                  <span>Duration: {formatDuration(callDuration)}</span>
                  <span className="flex items-center gap-1">
                    <Users className="w-3 h-3" />
                    {participants.length} participant{participants.length !== 1 ? 's' : ''}
                  </span>
                </div>
                
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    connectionStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'
                  }`}></div>
                  <span className="capitalize">{connectionStatus}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}