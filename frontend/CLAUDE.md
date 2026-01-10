# Seven Ultimate Productivity System - Claude Code Configuration

## 🎯 System Overview

This repository implements a comprehensive productivity system with:
- **3 specialized subagents** for different tasks (conversation-searcher, context-enhancer, link-generator)
- **25M+ word conversation database** with full-text search
- **Automatic GitHub issue enhancement** with conversation context
- **Simple CRM pipeline** using GitHub Projects
- **Action-oriented responses** with direct links and follow-ups

## 🤖 Subagent Integration

### **When to Use Subagents**

**Always use subagents for these tasks:**
- **Research/Search**: Use `conversation-searcher` subagent for finding related discussions
- **Context Enhancement**: Use `context-enhancer` for adding conversation context to issues
- **Response Enhancement**: Use `link-generator` for creating action links and follow-ups

### **Subagent Usage Patterns**

```markdown
# For searching past conversations
@conversation-searcher find discussions about "JWT authentication"

# For enhancing GitHub issues with context  
@context-enhancer add context to this issue about user onboarding

# For creating actionable responses
@link-generator enhance this task completion with action links
```

## 📋 Response Enhancement Standards

### **Task Completion Format**

When completing any task, **ALWAYS** follow this enhanced format:

```markdown
## ✅ [Task Description] - Completed Successfully!

### 🔗 **Quick Actions**
- **[📖 View [filename]](./path/to/file)** - Review the complete result
- **[✏️ Edit [filename]](https://github.com/Arnarsson/Seven/edit/main/path/to/file)** - Make changes
- **[📋 Copy Content](javascript:navigator.clipboard.writeText('content'))** - Copy to clipboard

### 📧 **Communication** (when applicable)
- **[📤 Send Email](mailto:contact@email.com?subject=Subject&body=Pre-filled)** - Ready to send
- **[💼 Connect on LinkedIn](https://linkedin.com/in/profile)** - Professional connection
- **[📅 Schedule Meeting](https://calendly.com/link)** - Set up call

### 📋 **Follow-up Tasks**
- **[⏰ Day 3 Check-in](./issues/new?title=Check%20on%20[task]&labels=reminder)** - Gentle reminder
- **[📞 Week 1 Call](./issues/new?title=Follow%20up%20call&labels=call)** - Schedule follow-up
- **[📝 Next Steps](./issues/new?title=Next%20steps%20for%20[task]&labels=planning)** - Continue work

### 🧠 **Related Context** (when available)
Use @conversation-searcher to find and include relevant past discussions

### 📊 **Task Metrics**
- **Completion Time**: [X minutes/hours]
- **Files Created**: [number and list]
- **Next Milestone**: [specific next step]
- **Success Probability**: [estimated %]
```

## 🗂️ File Organization Standards

### **Naming Conventions**
- **Emails**: `{contact-name}-{purpose}-email.md`
- **Proposals**: `{company}-{service}-proposal.md`  
- **Meeting Notes**: `{date}-{contact}-meeting.md`
- **Documentation**: `{topic}-{type}.md`

### **File Locations**
- **Conversations/Communications**: Root directory or `communications/`
- **Documentation**: `docs/` or root directory
- **Scripts and Tools**: `scripts/`
- **Templates**: `templates/` (create if needed)

## 👤 Contact Management Integration

### **When People/Companies Are Mentioned**

**Automatic Actions:**
1. **Extract contact details** (name, company, email, potential deal value)
2. **Search conversation history** using @conversation-searcher
3. **Create contact tracking issue** if new contact:
   ```markdown
   [👤 Track Contact](./issues/new?title=Contact:%20[Name]%20at%20[Company]&template=contact.md&labels=contact,pipeline)
   ```

### **Contact Issue Template**
```markdown
## Contact: [Name] at [Company]

**Status**: Cold/Warm/Proposal/Won/Lost
**Deal Value**: [Amount] DKK (estimated)
**Email**: [email if known]
**LinkedIn**: [profile if found]

### Background
- How we connected: [context]
- Their interest: [what they need]
- Our solution: [what we can offer]

### Next Actions
- [ ] Send introduction email
- [ ] Research their company needs
- [ ] Prepare customized proposal
- [ ] Schedule discovery call

### Related Conversations
[Auto-populated by context-enhancer subagent]
```

## 🔍 Search Integration

### **Before Major Tasks**

**Always search for related context first:**
1. Use @conversation-searcher to find previous discussions
2. Include relevant insights in your response
3. Avoid duplicating previous work
4. Reference past decisions and learnings

### **Search Query Examples**
- Technical topics: `@conversation-searcher "React authentication patterns"`
- Business topics: `@conversation-searcher "SaaS pricing strategy"`
- People: `@conversation-searcher "John from TechCorp"`
- Decisions: `@conversation-searcher "why we chose PostgreSQL"`

## 📊 GitHub Projects Integration

### **Issue Labels for Pipeline Management**
- `contact` - New lead or business contact
- `proposal` - Active proposal stage
- `follow-up` - Needs follow-up action
- `won` - Successfully closed deal
- `lost` - Lost opportunity
- `reminder` - Scheduled reminder task
- `call` - Phone call needed
- `email` - Email action required

### **Pipeline Stages**
1. **Cold** - Initial contact, research phase
2. **Warm** - Active discussion, building relationship
3. **Proposal** - Formal proposal sent
4. **Won** - Deal closed successfully
5. **Lost** - Opportunity lost, learn from it

## ⚡ Automation Features

### **GitHub Actions Integration**
- **New issues** automatically get context from conversation history
- **Only human-created issues** are enhanced (not bot issues)
- **Professional formatting** with clear attribution

### **Conversation Database**
- **25M+ words** of searchable conversation history
- **ChatGPT + Claude** conversations included
- **Full-text search** with relevance ranking
- **Auto-imported** from exports

## 🎯 Success Metrics

### **Response Quality Indicators**
- ✅ Direct action links included
- ✅ Relevant conversation context provided
- ✅ Clear next steps defined
- ✅ Contact information extracted and tracked
- ✅ Follow-up automation created

### **Productivity Measurements**
- **Context Discovery**: Time saved finding previous discussions
- **Action Completion**: Click-through rate on action links
- **Follow-up Success**: Completion rate of automated reminders
- **Deal Pipeline**: Conversion rate from cold to won

## 🔧 Technical Notes

### **Database Structure**
- SQLite database at `data/seven.db`
- Full-text search enabled
- Contact and task tracking tables
- GitHub issues sync capability

### **Subagent Architecture**
- Independent context windows for each agent
- Specialized prompts for different domains
- Automatic delegation based on task type
- Coordinated results integration

## 💡 Best Practices

### **For Every Task**
1. **Search first** - Check conversation history before starting
2. **Document decisions** - Explain reasoning for future reference
3. **Create actions** - Always provide next steps and follow-ups
4. **Track contacts** - Extract and manage relationship information
5. **Link everything** - Connect related issues, conversations, and tasks

### **Quality Standards**
- **Accuracy**: All links must work correctly
- **Completeness**: Include all relevant context and actions
- **Professionalism**: Maintain business-appropriate tone
- **Efficiency**: Minimize clicks needed for common actions
- **Intelligence**: Learn from past conversations and decisions

---

**Remember**: This system transforms GitHub into a comprehensive productivity platform. Every interaction should leverage the conversation database, create actionable outcomes, and build toward long-term relationship and project success.