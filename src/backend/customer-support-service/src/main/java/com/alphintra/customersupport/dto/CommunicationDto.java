package com.alphintra.customersupport.dto;

import com.alphintra.customersupport.entity.CommunicationType;
import com.alphintra.customersupport.entity.SenderType;

import java.time.LocalDateTime;
import java.util.List;

/**
 * DTO for communication information.
 */
public class CommunicationDto {

    private Long communicationId;
    private String ticketId;
    private String senderId;
    private String senderName;
    private SenderType senderType;
    private String content;
    private CommunicationType communicationType;
    private Boolean isInternal;
    private List<String> attachments;
    private LocalDateTime createdAt;
    private LocalDateTime readAt;
    private String emailMessageId;
    private Integer phoneCallDuration;
    private String videoCallRecordingUrl;

    // Additional display fields
    private String senderDisplayName;
    private String typeDisplayName;
    private boolean isRead;
    private String formattedCreatedAt;
    private String formattedDuration;

    // Constructors
    public CommunicationDto() {}

    // Getters and Setters
    public Long getCommunicationId() {
        return communicationId;
    }

    public void setCommunicationId(Long communicationId) {
        this.communicationId = communicationId;
    }

    public String getTicketId() {
        return ticketId;
    }

    public void setTicketId(String ticketId) {
        this.ticketId = ticketId;
    }

    public String getSenderId() {
        return senderId;
    }

    public void setSenderId(String senderId) {
        this.senderId = senderId;
    }

    public String getSenderName() {
        return senderName;
    }

    public void setSenderName(String senderName) {
        this.senderName = senderName;
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

    public String getSenderDisplayName() {
        return senderDisplayName;
    }

    public void setSenderDisplayName(String senderDisplayName) {
        this.senderDisplayName = senderDisplayName;
    }

    public String getTypeDisplayName() {
        return typeDisplayName;
    }

    public void setTypeDisplayName(String typeDisplayName) {
        this.typeDisplayName = typeDisplayName;
    }

    public boolean isRead() {
        return isRead;
    }

    public void setRead(boolean read) {
        isRead = read;
    }

    public String getFormattedCreatedAt() {
        return formattedCreatedAt;
    }

    public void setFormattedCreatedAt(String formattedCreatedAt) {
        this.formattedCreatedAt = formattedCreatedAt;
    }

    public String getFormattedDuration() {
        return formattedDuration;
    }

    public void setFormattedDuration(String formattedDuration) {
        this.formattedDuration = formattedDuration;
    }

    // Utility methods
    public boolean isFromUser() {
        return senderType == SenderType.USER;
    }

    public boolean isFromAgent() {
        return senderType == SenderType.AGENT;
    }

    public boolean isSystemGenerated() {
        return senderType == SenderType.SYSTEM;
    }

    public boolean hasAttachments() {
        return attachments != null && !attachments.isEmpty();
    }
}