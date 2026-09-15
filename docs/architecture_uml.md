# RuinionAI - Architecture SaaS V1

Ce document sert de suivi pour le modele de donnees cible de la V1 SaaS.

```mermaid
classDiagram
    class User {
        int id
        string first_name
        string last_name
        string email
        string password_hash
        bool is_active
        datetime created_at
        datetime updated_at
    }

    class Organization {
        int id
        string name
        datetime created_at
        datetime updated_at
    }

    class OrganizationMember {
        int id
        int organization_id
        int user_id
        enum role
        datetime created_at
        datetime updated_at
    }

    class Meeting {
        int id
        int organization_id
        int created_by_user_id
        string title
        text participants
        text transcription
        text summary_short
        text summary_long
        datetime date
        datetime created_at
        datetime updated_at
    }

    class MeetingDecision {
        int id
        int meeting_id
        text content
        datetime created_at
    }

    class MeetingActionItem {
        int id
        int meeting_id
        text content
        string assignee_name
        datetime due_date
        enum status
        datetime created_at
        datetime updated_at
    }

    class MeetingQuestion {
        int id
        int meeting_id
        text content
        datetime created_at
    }

    User "1" --> "0..*" OrganizationMember : belongs through
    Organization "1" --> "0..*" OrganizationMember : has members
    Organization "1" --> "0..*" Meeting : owns
    User "1" --> "0..*" Meeting : creates
    Meeting "1" --> "0..*" MeetingDecision : has
    Meeting "1" --> "0..*" MeetingActionItem : has
    Meeting "1" --> "0..*" MeetingQuestion : has
```

## Regles V1

- Un utilisateur peut appartenir a une ou plusieurs organisations.
- Une organisation peut avoir plusieurs utilisateurs.
- Le role d'un utilisateur dans une organisation est stocke dans `organization_members`.
- Une reunion appartient toujours a une organisation.
- Une reunion garde aussi l'utilisateur qui l'a creee via `created_by_user_id`.
- Les participants d'une reunion restent un champ texte pour la V1.
- Les decisions, actions et questions peuvent etre ajoutees apres la base auth.

