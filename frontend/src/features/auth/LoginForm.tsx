import { useState } from "react"

type LoginFormProps = {
  onSubmit: (email: string, password: string) => Promise<void>
  loading: boolean
}

export function LoginForm({ onSubmit, loading }: LoginFormProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  return (
    <form
      className="card form-card"
      onSubmit={async (event) => {
        event.preventDefault()
        await onSubmit(email, password)
      }}
    >
      <h2>Login</h2>
      <p>
        Use as credenciais seed descritas no README apenas para ambiente local.
      </p>
      <label>
        E-mail
        <input
          placeholder="admin@crmimobiliaria.local"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          type="email"
        />
      </label>
      <label>
        Senha
        <input
          placeholder="••••••••"
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
