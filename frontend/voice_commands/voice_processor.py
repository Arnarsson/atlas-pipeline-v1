#!/usr/bin/env python3
"""
Voice Command Processor for Seven Productivity System
Processes natural language commands and executes appropriate actions
"""

import re
import json
from typing import Dict, List, Tuple

class VoiceCommandProcessor:
    def __init__(self):
        self.command_patterns = {
            'create_task': [
                r'create (?:a )?task to (.+)',
                r'add (?:a )?task (?:to )?(.+)',
                r'new task (?:for )?(.+)',
                r'make (?:a )?task (?:to )?(.+)'
            ],
            'show_status': [
                r'show (?:me )?(?:the )?status (?:of )?(.+)',
                r'what(?:\'s| is) (?:the )?status (?:of )?(.+)',
                r'how(?:\'s| is) (.+) (?:going|doing|progressing)'
            ],
            'focus_today': [
                r'what should I (?:work on|focus on|do) today',
                r'(?:show )?(?:me )?today(?:\'s)? (?:tasks|agenda|priorities)',
                r'what(?:\'s)? (?:on )?(?:my )?(?:agenda|schedule) (?:for )?today'
            ],
            'project_context': [
                r'(?:load|show|get) (?:context )?(?:for )?(.+)',
                r'tell me about (.+)',
                r'what do (?:I|we) know about (.+)'
            ],
            'schedule_reminder': [
                r'(?:schedule|set|create) (?:a )?reminder (?:to )?(.+)',
                r'remind me (?:to )?(.+)',
                r'don(?:\'t)? forget (?:to )?(.+)'
            ]
        }
        
        self.project_keywords = {
            'seven': ['seven', 'ai agent', 'system management', 'productivity'],
            'allign': ['allign', 'construction', 'mobile app', 'time tracking'],
            'harka': ['harka', 'training platform', 'investor'],
            'atlas': ['atlas', 'daniel', 'client', 'deployment']
        }
    
    def process_command(self, command: str) -> Dict:
        """Process natural language command and return structured action"""
        command = command.lower().strip()
        
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command)
                if match:
                    return self.execute_command(command_type, match.groups(), command)
        
        return {
            'action': 'unknown',
            'message': 'I didn\'t understand that command. Try something like "create a task to..." or "show me today\'s priorities"'
        }
    
    def execute_command(self, command_type: str, groups: Tuple, original_command: str) -> Dict:
        """Execute the identified command"""
        
        if command_type == 'create_task':
            return self.create_task_command(groups[0])
            
        elif command_type == 'show_status':
            return self.show_status_command(groups[0])
            
        elif command_type == 'focus_today':
            return self.focus_today_command()
            
        elif command_type == 'project_context':
            return self.project_context_command(groups[0])
            
        elif command_type == 'schedule_reminder':
            return self.schedule_reminder_command(groups[0])
        
        return {'action': 'unknown', 'message': 'Command not implemented yet'}
    
    def create_task_command(self, task_description: str) -> Dict:
        """Process task creation command"""
        # Import the Claude Intelligence Layer
        from claude_intelligence import intelligence
        
        task_data = intelligence.analyze_natural_language_task(task_description)
        
        return {
            'action': 'create_task',
            'task_data': task_data,
            'message': f'Creating task: {task_data["title"]}',
            'github_issue': {
                'title': task_data['title'],
                'body': self.generate_task_body(task_data),
                'labels': task_data['labels']
            }
        }
    
    def generate_task_body(self, task_data: Dict) -> str:
        """Generate GitHub issue body from task data"""
        priority_emoji = {
            'high': '🎯',
            'medium': '⚡',
            'low': '📝'
        }
        
        return f"""## Priority: {priority_emoji.get(task_data['priority'], '⚡')} {task_data['priority'].upper()}
**Project:** {task_data['project']}
**Estimated Time:** {task_data['estimated_time']} minutes

### Task Description
{task_data.get('description', 'Task created via voice command')}

### Success Criteria
{chr(10).join(task_data['success_criteria'])}

### Categories
{', '.join(task_data['categories'])}

---
*Created via Seven Voice Command System*
"""
    
    def show_status_command(self, project: str) -> Dict:
        """Show project status"""
        return {
            'action': 'show_status',
            'project': project,
            'message': f'Showing status for {project}',
            'github_query': {
                'query': f'is:issue label:{project.upper()}',
                'action': 'list_issues'
            }
        }
    
    def focus_today_command(self) -> Dict:
        """Generate today's focus recommendations"""
        return {
            'action': 'focus_today',
            'message': 'Generating today\'s focus recommendations',
            'github_query': {
                'query': 'is:issue is:open sort:updated',
                'action': 'prioritize_today'
            }
        }
    
    def project_context_command(self, project: str) -> Dict:
        """Load project context"""
        return {
            'action': 'project_context',
            'project': project,
            'message': f'Loading context for {project}',
            'memory_action': {
                'action': 'search_context',
                'query': project
            }
        }
    
    def schedule_reminder_command(self, reminder: str) -> Dict:
        """Schedule a reminder"""
        return {
            'action': 'schedule_reminder',
            'reminder': reminder,
            'message': f'Scheduling reminder: {reminder}',
            'github_issue': {
                'title': f'⏰ REMINDER: {reminder}',
                'body': f'Automated reminder: {reminder}',
                'labels': ['⏰ reminder', '🤖 automation']
            }
        }

# Example usage
if __name__ == "__main__":
    processor = VoiceCommandProcessor()
    
    # Test commands
    test_commands = [
        "Create a task to implement real-time GPS tracking in Allign",
        "Show me HARKA project status",
        "What should I focus on today?",
        "Load context for Seven AI agents",
        "Schedule a reminder to check Atlas deployment on Monday"
    ]
    
    for command in test_commands:
        result = processor.process_command(command)
        print(f"Command: {command}")
        print(f"Result: {result}")
        print("-" * 50)
