package com.alphintra.customersupport.dto;

import com.alphintra.customersupport.entity.AgentLevel;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * DTO for ticket escalation.
 */
public class EscalationDto {

    @NotNull(message = "Target level is required")
    private AgentLevel targetLevel;

    @NotBlank(message = "Reason is required")
    private String reason;

    private String targetDepartment;
    private String notes;

    // Constructors
    public EscalationDto() {}

    public EscalationDto(AgentLevel targetLevel, String reason) {
        this.targetLevel = targetLevel;
        this.reason = reason;
    }

    // Getters and Setters
    public AgentLevel getTargetLevel() {
        return targetLevel;
    }

    public void setTargetLevel(AgentLevel targetLevel) {
        this.targetLevel = targetLevel;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }

    public String getTargetDepartment() {
        return targetDepartment;
    }

    public void setTargetDepartment(String targetDepartment) {
        this.targetDepartment = targetDepartment;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }
}