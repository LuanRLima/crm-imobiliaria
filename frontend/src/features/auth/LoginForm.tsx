import { useState } from "react"

type LoginFormProps = {
  onSubmit: (email: string, password: string) => Promise<void>
  loading: boolean
}

export function LoginForm({ onSubmit, loading }: LoginFormProps) {
  const [email, setEmail] = useState("admin@crmimobiliaria.local")
  const [password, setPassword] = useState("Admin123!")

  return (
    <form
      className="card form-card"
      onSubmit={async (event) => {
        event.preventDefault()
        await onSubmit(email, password)
      }}
    >
      <h2>Login</h2>
      <label>
        E-mail
        <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
      </label>
      <label>
        Senha
        <input
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          type="password"
        />
      </label>
      <button disabled={loading} type="submit">
        {loading ? "Entrando..." : "Entrar"}
      </button>
    </form>
  )
}
