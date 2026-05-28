import { useEffect, useState } from 'react'
import { Upload, Plus, X, Briefcase, Code, User, Star } from 'lucide-react'
import api from '../api/client'

export default function Profile() {
  const [skills, setSkills] = useState([])
  const [skillInput, setSkillInput] = useState('')
  const [roles, setRoles] = useState([])
  const [roleInput, setRoleInput] = useState('')
  const [bio, setBio] = useState('')
  const [experienceYears, setExperienceYears] = useState(1)
  const [resumeFile, setResumeFile] = useState(null)
  const [projects, setProjects] = useState([])
  const [newProject, setNewProject] = useState({
    name: '', description: '', tech_stack: [], url: ''
  })
  const [techInput, setTechInput] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [extractedCount, setExtractedCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/profile/').then(res => {
      if (res.data) {
        setSkills(res.data.skills || [])
        setRoles(res.data.target_roles || [])
        setBio(res.data.bio || '')
        setExperienceYears(res.data.experience_years || 1)
        setProjects(res.data.projects || [])
      }
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const addSkill = () => {
    const s = skillInput.trim()
    if (s && !skills.includes(s)) {
      setSkills(prev => [...prev, s])
      setSkillInput('')
    }
  }
  const addRole = () => {
    const r = roleInput.trim()
    if (r && !roles.includes(r)) {
      setRoles(prev => [...prev, r])
      setRoleInput('')
    }
  }
  const addTechToProject = () => {
    const t = techInput.trim()
    if (t && !newProject.tech_stack.includes(t)) {
      setNewProject(p => ({ ...p, tech_stack: [...p.tech_stack, t] }))
      setTechInput('')
    }
  }
  const addProject = async () => {
    if (!newProject.name.trim()) return
    try {
      const fd = new FormData()
      fd.append('name', newProject.name)
      fd.append('description', newProject.description)
      fd.append('tech_stack', JSON.stringify(newProject.tech_stack))
      fd.append('url', newProject.url)
      const res = await api.post('/api/profile/project/add', fd)
      setProjects(prev => [
        ...prev,
        { ...newProject, tech_stack: res.data.tech_stack || newProject.tech_stack },
      ])
      setNewProject({ name: '', description: '', tech_stack: [], url: '' })
      setTechInput('')
    } catch (e) {
      console.error(e)
    }
  }

  const save = async () => {
    setSaving(true)
    try {
      const fd = new FormData()
      fd.append('skills', JSON.stringify(skills))
      fd.append('target_roles', JSON.stringify(roles))
      fd.append('experience_years', String(experienceYears))
      fd.append('bio', bio)
      const res = await api.post('/api/profile/update', fd)
      if (resumeFile) {
        const rfd = new FormData()
        rfd.append('file', resumeFile)
        rfd.append('set_as_primary', 'true')
        const up = await api.post('/api/profile/resume/upload', rfd)
        setExtractedCount(up.data.skill_count || 0)
      }
      if (res.data.skills) {
        setSkills(res.data.skills)
        if (!resumeFile) {
          setExtractedCount(res.data.total_skills || res.data.skills.length)
        }
      }
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e) {
      console.error(e)
    } finally { setSaving(false) }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-gray-500">Loading profile...</div>
    </div>
  )

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Your Profile</h1>
        <p className="text-gray-400 text-sm">
          The AI agent uses everything here to find and score jobs for you
        </p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <User size={16} className="text-sky-400" />
          <h2 className="text-white font-medium">About You</h2>
        </div>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-gray-400 text-xs mb-1 block">
              Experience (years)
            </label>
            <input type="number" min="0" max="50"
              value={experienceYears}
              onChange={e => setExperienceYears(Number(e.target.value))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500" />
          </div>
        </div>
        <label className="text-gray-400 text-xs mb-1 block">
          Bio / Summary (optional)
        </label>
        <textarea
          value={bio}
          onChange={e => setBio(e.target.value)}
          placeholder="Brief summary of your background and goals..."
          rows={3}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-sky-500 resize-none"
        />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Upload size={16} className="text-sky-400" />
          <h2 className="text-white font-medium">Resume</h2>
          <span className="text-xs text-gray-500">
            Skills auto-extracted on upload
          </span>
        </div>
        <label className="flex flex-col items-center gap-3 border-2 border-dashed border-gray-700 rounded-xl p-8 cursor-pointer hover:border-sky-500 transition-colors">
          <Upload size={24} className="text-gray-500" />
          <span className="text-gray-400 text-sm">
            {resumeFile ? resumeFile.name : 'Upload PDF or DOCX'}
          </span>
          <input type="file" accept=".pdf,.docx" className="hidden"
            onChange={e => setResumeFile(e.target.files[0])} />
        </label>
        {extractedCount > 0 && (
          <p className="text-green-400 text-xs mt-2">
            Auto-extracted {extractedCount} skills from your resume
          </p>
        )}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Star size={16} className="text-sky-400" />
          <h2 className="text-white font-medium">Skills</h2>
          <span className="text-xs text-gray-500">
            Auto-populated from resume + projects
          </span>
        </div>
        <div className="flex gap-2 mb-3">
          <input value={skillInput}
            onChange={e => setSkillInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addSkill()}
            placeholder="Python, React, Docker..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-sky-500" />
          <button onClick={addSkill}
            className="bg-sky-600 hover:bg-sky-500 text-white px-3 py-2 rounded-lg">
            <Plus size={16} />
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {skills.map((s, i) => (
            <span key={i}
              className="flex items-center gap-1.5 bg-gray-800 text-gray-200 text-xs px-3 py-1.5 rounded-full">
              {s}
              <button onClick={() => setSkills(skills.filter((_, j) => j !== i))}>
                <X size={12} className="text-gray-400 hover:text-red-400" />
              </button>
            </span>
          ))}
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Briefcase size={16} className="text-sky-400" />
          <h2 className="text-white font-medium">Target Roles</h2>
        </div>
        <div className="flex gap-2 mb-3">
          <input value={roleInput}
            onChange={e => setRoleInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addRole()}
            placeholder="ML Engineer, Backend Dev..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-sky-500" />
          <button onClick={addRole}
            className="bg-sky-600 hover:bg-sky-500 text-white px-3 py-2 rounded-lg">
            <Plus size={16} />
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {roles.map((r, i) => (
            <span key={i}
              className="flex items-center gap-1.5 bg-sky-900/40 text-sky-300 text-xs px-3 py-1.5 rounded-full">
              {r}
              <button onClick={() => setRoles(roles.filter((_, j) => j !== i))}>
                <X size={12} className="text-sky-400 hover:text-red-400" />
              </button>
            </span>
          ))}
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Code size={16} className="text-sky-400" />
          <h2 className="text-white font-medium">Projects</h2>
          <span className="text-xs text-gray-500">
            Skills auto-extracted from projects
          </span>
        </div>

        {projects.map((p, i) => (
          <div key={i} className="bg-gray-800 rounded-lg p-4 mb-3 relative">
            <button
              onClick={() => setProjects(projects.filter((_, j) => j !== i))}
              className="absolute top-3 right-3 text-gray-500 hover:text-red-400">
              <X size={14} />
            </button>
            <p className="text-white text-sm font-medium">{p.name}</p>
            <p className="text-gray-400 text-xs mt-1">{p.description}</p>
            <div className="flex flex-wrap gap-1 mt-2">
              {p.tech_stack?.map((t, j) => (
                <span key={j} className="bg-gray-700 text-gray-300 text-xs px-2 py-0.5 rounded">
                  {t}
                </span>
              ))}
            </div>
          </div>
        ))}

        <div className="border border-gray-700 rounded-lg p-4 space-y-3">
          <p className="text-gray-400 text-xs font-medium">Add Project</p>
          <input
            value={newProject.name}
            onChange={e => setNewProject(p => ({ ...p, name: e.target.value }))}
            placeholder="Project name"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-sky-500" />
          <textarea
            value={newProject.description}
            onChange={e => setNewProject(p => ({ ...p, description: e.target.value }))}
            placeholder="What does it do? What problem does it solve?"
            rows={2}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-sky-500 resize-none" />
          <input
            value={newProject.url}
            onChange={e => setNewProject(p => ({ ...p, url: e.target.value }))}
            placeholder="GitHub URL (optional)"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-sky-500" />
          <div className="flex gap-2">
            <input
              value={techInput}
              onChange={e => setTechInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addTechToProject()}
              placeholder="Add tech (Python, React...)"
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-sky-500" />
            <button onClick={addTechToProject}
              className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg">
              <Plus size={16} />
            </button>
          </div>
          <div className="flex flex-wrap gap-1">
            {newProject.tech_stack.map((t, i) => (
              <span key={i} className="flex items-center gap-1 bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded">
                {t}
                <button onClick={() => setNewProject(p => ({
                  ...p,
                  tech_stack: p.tech_stack.filter((_, j) => j !== i)
                }))}>
                  <X size={10} />
                </button>
              </span>
            ))}
          </div>
          <button onClick={addProject}
            disabled={!newProject.name.trim()}
            className="w-full bg-gray-700 hover:bg-gray-600 text-white rounded-lg py-2 text-sm transition-colors disabled:opacity-50">
            Add Project
          </button>
        </div>
      </div>

      <button onClick={save} disabled={saving}
        className="w-full bg-sky-600 hover:bg-sky-500 text-white rounded-xl py-3 font-medium transition-colors disabled:opacity-50">
        {saving ? 'Saving & extracting skills...' : saved ? 'Saved!' : 'Save Profile'}
      </button>
    </div>
  )
}
