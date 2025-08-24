package com.alphintra.customersupport.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Entity representing communication within a support ticket.
 */
@Entity
@Table(name = "communications", indexes = {
    @Index(name = "idx_communication_ticket_created", columnList = "ticket_id, created_at"),
    @Index(name = "idx_communication_sender", columnList = "sender_id"),
    @Index(name = "idx_communication_type", columnList = "communication_type")
})
public class Communication {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "communication_id")
    private Long communicationId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "ticket_id", nullable = false)
    private Ticket ticket;

    @Column(name = "sender_id", nullable = false)
    private String senderId;

    @Enumerated(EnumType.STRING)
    @Column(name = "sender_type", nullable = false)
    private SenderType senderType;

    @Column(name = "content", columnDefinition = "TEXT")
    private String content;

    @Enumerated(EnumType.STRING)
    @Column(name = "communication_type", nullable = false)
    private CommunicationType communicationType;

    @Column(name = "is_internal", nullable = false)
    private Boolean isInternal = false;

    @ElementCollection
    @CollectionTable(name = "communication_attachments", 
                    joinColumns = @JoinColumn(name = "communication_id"))
    @Column(name = "attachment_url")
    private List<String> attachments = new ArrayList<>();

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "read_at")
    private LocalDateTime readAt;

    @Column(name = "email_message_id")
    private String emailMessageId;

    @Column(name = "phone_call_duration")
    private Integer phoneCallDuration; // in seconds

    @Column(name = "video_call_recording_url")
    private String videoCallRecordingUrl;

    // Constructors
    public Communication() {}

    public Communication(Ticket ticket, String senderId, SenderType senderType, 
                        String content, CommunicationType communicationType) {
        this.ticket = ticket;
        this.senderId = senderId;
        this.senderType = senderType;
        this.content = content;
        this.communicationType = communicationType;
        this.isInternal = false;
    }

    // Getters and Setters
    public Long getCommunicationId() {
        return communicationId;
    }

    public void setCommunicationId(Long communicationId) {
        this.communicationId = communicationId;
    }

    public Ticket getTicket() {
        return ticket;
    }

    public void setTicket(Ticket ticket) {
        this.ticket = ticket;
    }

    public String getSenderId() {
        return senderId;
    }

    public void setSenderId(String senderId) {
        this.senderId = senderId;
    }

    public SenderType getSenderType() {
        return senderType;
    }

    public void setSenderType(SenderType senderType) {
        this.senderType = senderType;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public CommunicationType getCommunicationType() {
        return communicationType;
    }

    public void setCommunicationType(CommunicationType communicationType) {
        this.communicationType = communicationType;
    }

    public Boolean getIsInternal() {
        return isInternal;
    }

    public void setIsInternal(Boolean isInternal) {
        this.isInternal = isInternal;
    }

    public List<String> getAttachments() {
        return attachments;
    }

    public void setAttachments(List<String> attachments) {
        this.attachments = attachments;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getReadAt() {
        return readAt;
    }

    public void setReadAt(LocalDateTime readAt) {
        this.readAt = readAt;
    }

    public String getEmailMessageId() {
        return emailMessageId;
    }

    public void setEmailMessageId(String emailMessageId) {
        this.emailMessageId = emailMessageId;
    }

    public Integer getPhoneCallDuration() {
        return phoneCallDuration;
    }

    public void setPhoneCallDuration(Integer phoneCallDuration) {
        this.phoneCallDuration = phoneCallDuration;
    }

    public String getVideoCallRecordingUrl() {
        return videoCallRecordingUrl;
    }

    public void setVideoCallRecordingUrl(String videoCallRecordingUrl) {
        this.videoCallRecordingUrl = videoCallRecordingUrl;
    }

    // Utility methods
    public void addAttachment(String attachmentUrl) {
        this.attachments.add(attachmentUrl);
    }

    public void markAsRead() {
        this.readAt = LocalDateTime.now();
    }

    public boolean isRead() {
        return readAt != null;
    }

    public boolean isFromUser() {
        return senderType == SenderType.USER;
    }

    public boolean isFromAgent() {
        return senderType == SenderType.AGENT;
    }

    public boolean isSystemGenerated() {
        return senderType == SenderType.SYSTEM;
    }
}