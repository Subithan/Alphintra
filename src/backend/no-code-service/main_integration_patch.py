#!/usr/bin/env python3
"""
Integration patch for main.py to use Enhanced Strategy Handler

This file contains the code updates needed to integrate the Enhanced Strategy Handler
with the existing main.py execution flow.
"""

# ADD THIS IMPORT at the top of main.py after other imports:
"""
from enhanced_strategy_handler import execute_enhanced_strategy_mode
"""

# REPLACE the existing strategy mode section (lines ~550-585) with this enhanced version:
"""
        if request.mode == "strategy":
            # Enhanced Strategy mode: Use Enhanced Compiler with organized file storage
            logger.info(f"Processing workflow {workflow_id} in enhanced strategy mode")

            try:
                # Use Enhanced Strategy Handler
                strategy_result = execute_enhanced_strategy_mode(
                    workflow=workflow,
                    execution_config=request.config,
                    db=db
                )

                if strategy_result['success']:
                    # Strategy generated and saved successfully
                    logger.info(f"Enhanced strategy generated successfully: {strategy_result['strategy_details']['filename']}")
                    
                    return {
                        "execution_id": strategy_result['execution_id'],
                        "mode": "strategy", 
                        "status": "completed",
                        "message": strategy_result['message'],
                        "next_action": f"/api/workflows/{workflow_id}/generated-code",
                        "strategy_details": {
                            "filename": strategy_result['strategy_details']['filename'],
                            "file_path": strategy_result['strategy_details']['file_path'],
                            "lines_of_code": strategy_result['strategy_details']['lines_of_code'],
                            "requirements": strategy_result['strategy_details']['requirements'],
                            "compilation_stats": strategy_result['strategy_details']['compilation_stats']
                        },
                        "execution_record_id": strategy_result['execution_record_id']
                    }
                else:
                    # Strategy generation failed
                    logger.error(f"Enhanced strategy generation failed: {strategy_result.get('error', 'Unknown error')}")
                    
                    return {
                        "execution_id": strategy_result['execution_id'],
                        "mode": "strategy",
                        "status": "failed", 
                        "error": strategy_result.get('error', 'Strategy generation failed'),
                        "details": strategy_result.get('details', {}),
                        "next_action": None
                    }
                    
            except Exception as e:
                logger.error(f"Exception in enhanced strategy mode: {str(e)}")
                workflow.compilation_status = 'generation_failed'
                workflow.compilation_errors = [{"type": "exception", "message": str(e)}]
                db.commit()
                
                return {
                    "execution_id": str(uuid.uuid4()),
                    "mode": "strategy",
                    "status": "failed",
                    "error": f"Strategy execution failed: {str(e)}",
                    "next_action": None
                }
"""

# ADD these new API endpoints after the existing routes:
"""
@app.get("/api/workflows/strategies/list")
async def list_user_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    '''List all generated strategies for the current user'''
    from enhanced_strategy_handler import EnhancedStrategyHandler
    
    try:
        handler = EnhancedStrategyHandler()
        strategies = handler.list_generated_strategies(current_user.id, db)
        
        return {
            "success": True,
            "strategies": strategies['strategies'],
            "total_count": strategies['total_count']
        }
        
    except Exception as e:
        logger.error(f"Error listing user strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list strategies: {str(e)}")


@app.get("/api/workflows/{workflow_id}/strategy-details")
async def get_strategy_details(
    workflow_id: str,
    execution_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    '''Get detailed information about a generated strategy'''
    from enhanced_strategy_handler import EnhancedStrategyHandler
    
    try:
        handler = EnhancedStrategyHandler()
        details = handler.get_strategy_details(workflow_id, execution_id, db)
        
        if not details['success']:
            raise HTTPException(status_code=404, detail=details['error'])
            
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get strategy details: {str(e)}")


@app.get("/api/workflows/strategies/files-overview")  
async def get_strategy_files_overview(
    current_user: User = Depends(get_current_user)
):
    '''Get overview of generated strategy files'''
    from output_manager import OutputManager
    
    try:
        manager = OutputManager()
        
        # Get file statistics
        stats = manager.get_folder_stats()
        files = manager.list_generated_files()
        
        return {
            "success": True,
            "file_overview": {
                "total_files": stats['total']['file_count'],
                "total_size_mb": stats['total']['total_size_mb'],
                "by_category": {
                    mode: {
                        "file_count": mode_stats['file_count'],
                        "size_mb": mode_stats['total_size_mb']
                    }
                    for mode, mode_stats in stats.items() if mode != 'total'
                },
                "recent_files": {
                    mode: [Path(f).name for f in file_list[:3]]  # Show 3 most recent
                    for mode, file_list in files.items()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting strategy files overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get files overview: {str(e)}")
"""

# UPDATE the API routes list in the welcome endpoint:
"""
        "api_routes": {
            # ... existing routes ...
            "list_strategies": "/api/workflows/strategies/list",
            "strategy_details": "/api/workflows/{workflow_id}/strategy-details",  
            "strategy_files_overview": "/api/workflows/strategies/files-overview"
        }
"""

if __name__ == "__main__":
    print("📝 Main.py Integration Patch")
    print("=" * 50)
    print("This file contains the code changes needed to integrate")
    print("the Enhanced Strategy Handler with main.py")
    print("\nChanges needed:")
    print("1. Add import for enhanced_strategy_handler")
    print("2. Replace strategy mode section with enhanced version")
    print("3. Add new API endpoints for strategy management") 
    print("4. Update API routes list")
    print("\n🎯 After applying these changes, the frontend will have:")
    print("✅ Enhanced strategy generation with organized file storage")
    print("✅ API endpoints to list and manage generated strategies")
    print("✅ Detailed strategy information and file statistics")
    print("✅ Improved error handling and logging")