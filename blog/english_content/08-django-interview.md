---
slug_fa: "django-interview-questions-with-short-answers"
slug_en: "django-interview-questions-with-short-answers"
title_en: "30 Django Interview Questions with Short Answers"
summary_en: "Review 30 Django interview questions on queries, migrations, forms, security, sessions, testing and deployment, with concise practical answers."
---
Preparing for a Django interview is about understanding behaviour, not memorising hundreds of answers. These 30 questions follow the nine areas in our Persian article: queries, models, views, forms, security, authentication, performance, testing and deployment. The selection is a revision aid, not an exhaustive interview syllabus or the contents of Rvion's assessment bank.

Answers refer to [Django 5.2 documentation](https://docs.djangoproject.com/en/5.2/). Check the documentation and [support schedule](https://www.djangoproject.com/download/) for the version used by your project. Be ready to explain an example and a failure case, not just a definition.

## ORM and queries

### 1. What does a lazy QuerySet mean?

Constructing and chaining filters normally does not execute SQL. Evaluation happens through operations such as iteration, `list()`, `len()`, `bool()` or `repr()`. A fully evaluated QuerySet caches its results; indexing an unevaluated QuerySet does not populate that full cache. See the [query guide](https://docs.djangoproject.com/en/5.2/topics/db/queries/).

### 2. How do select_related and prefetch_related differ?

`select_related()` uses joins for single-valued relations such as foreign keys. `prefetch_related()` uses additional queries and combines results in Python, supporting multi-valued relations as well. Choose based on access patterns rather than adding either indiscriminately.

```python
Book.objects.select_related("author")
Author.objects.prefetch_related("books")
```

### 3. When are F and Q expressions useful?

`F()` refers to database field values, allowing updates such as increments without a Python read-modify-write race. `Q()` combines conditions using AND, OR and NOT. Correct use still depends on the business rule and transaction requirements.

### 4. Do update and bulk_create call save and signals?

No. These bulk operations bypass each object's `save()` and its `pre_save` and `post_save` signals. Do not depend on that logic running implicitly. Review the [QuerySet reference](https://docs.djangoproject.com/en/5.2/ref/models/querysets/) for operation-specific limitations.

### 5. What do atomic and on_commit do?

An `atomic()` block commits or rolls back as a unit; nested blocks normally use savepoints. `on_commit()` registers work that should happen only after successful commit. Catch a database error outside the relevant inner atomic block if later queries must continue safely.

```python
with transaction.atomic():
    order.save()
    transaction.on_commit(lambda: send_receipt(order.pk))
```

## Models and migrations

### 6. How do null and blank differ?

`null` controls database storage; `blank` controls validation. Text fields usually use an empty string rather than a second empty representation, although unique, optional string fields can need special treatment. Read the [field reference](https://docs.djangoproject.com/en/5.2/ref/models/fields/).

### 7. What are the important on_delete options?

`CASCADE` deletes dependent objects; `PROTECT` blocks deletion. `RESTRICT` also blocks it but allows certain deletions within the same cascade operation. `SET_NULL` requires nullable storage, and `SET_DEFAULT` uses the default. Choose according to the data's lifecycle, not habit.

### 8. How do makemigrations and migrate differ?

`makemigrations` creates migration files from model changes; `migrate` applies or reverses them. Data migrations use operations such as `RunPython` and are written explicitly. Use historical models from the migration app registry, and define reversal where appropriate. See the [migration guide](https://docs.djangoproject.com/en/5.2/topics/migrations/).

## Views and URLs

### 9. Should every view be class-based?

No. Function-based and class-based views are alternatives. Classes can separate HTTP handlers and reuse mixins; a short function may be clearer for a simple flow. Prefer readable behaviour over inheritance for its own sake.

### 10. How is a URL resolved, and why name it?

Django checks URL patterns in order and uses the first match. Named routes allow `reverse()` and the template URL tag to construct links without repeating hardcoded paths throughout the application.

### 11. Does middleware order matter?

Yes. Requests pass through outer-to-inner layers and responses return in reverse. A middleware can return early and bypass later layers and the view. Dependencies such as sessions before authentication make ordering significant.

## Templates and forms

### 12. How does template inheritance work?

A child template uses `extends` and overrides named blocks. `block.super` includes the parent's block content. The syntax below is displayed literally; article content is not evaluated as a Django template.

```django
{% extends "base.html" %}
{% block content %}{{ block.super }}{% endblock %}
```

### 13. How does ModelForm differ from Form?

A `ModelForm` derives fields and some validation from a model. Declare editable fields explicitly. Automatically exposing every model field can accidentally permit changes to a sensitive field added later.

### 14. What is the validation sequence?

For each field, Django runs conversion, field validation and validators, followed by `clean_fieldname()` if appropriate. The form's `clean()` handles cross-field rules. Raise `ValidationError` and do not assume invalid fields exist in `cleaned_data`. See [form validation](https://docs.djangoproject.com/en/5.2/ref/forms/validation/).

## Security

### 15. How does CSRF protection work?

Django verifies a token against the CSRF secret for unsafe requests, along with applicable origin or referer checks. Templates can render a masked token. The secret is normally cookie-based, or stored in the session when configured that way. Keep GET free of state-changing actions; do not use exemptions as a routine repair.

### 16. How does the ORM reduce SQL injection risk?

Queries separate SQL from parameters. Risk returns when untrusted values are interpolated into raw SQL. Supply parameters separately and do not quote placeholders yourself. Review [Django security](https://docs.djangoproject.com/en/5.2/topics/security/).

```python
Person.objects.raw("SELECT * FROM myapp_person WHERE last_name = %s", [lname])
```

### 17. What does template autoescaping protect against?

It escapes variable output so characters are not normally interpreted as HTML markup. It is not a universal defence for every context. `safe`, `mark_safe` and disabled escaping can introduce XSS when used with untrusted content; sanitise permitted rich HTML deliberately.

## Authentication and sessions

### 18. How do authenticate and login differ?

`authenticate()` checks credentials through authentication backends and returns a user or `None`. `login()` establishes authenticated session state and handles session-key rotation or flushing as needed. Checking credentials alone does not log a browser in.

### 19. Is login_required enough for permissions?

No. It requires authentication, not ownership or a particular permission. Check permissions and object scope separately. Django's default model permissions cover add, change, delete and view; groups can share permissions among users.

### 20. When should a custom user model be introduced?

For a new project, a model based on `AbstractUser` can be selected with `AUTH_USER_MODEL` before the first migration. Changing it after tables and relationships exist is considerably more involved. Use the configured user model instead of assuming Django's default User everywhere.

### 21. Where are sessions stored?

The default backend stores session data in the database and keeps a key in the cookie. Other backends include cached database, cache, files and signed cookies. Signed-cookie content is signed, not encrypted; signing does not make confidential data unreadable.

## Performance and caching

### 22. How do you find the actual bottleneck?

Measure first: request timing, query counts, slow queries and realistic workload. A development tool can help locally, but production monitoring has different privacy and overhead constraints. Fix unnecessary work before using cache to conceal it. See [performance guidance](https://docs.djangoproject.com/en/5.2/topics/performance/).

### 23. Are count and exists always better than len?

They are efficient when you need only a count or existence check. If the QuerySet is already evaluated, or you will immediately fetch every result anyway, an extra query may be unnecessary. Choose based on what the code actually needs.

### 24. What caching levels are available?

Django supports site, view, template-fragment and low-level caching. Backends include Redis, Memcached, database, files and local memory. Local-memory cache is per process, not a shared cross-worker store. Define invalidation and isolation, especially for personalised pages.

## Testing

### 25. How do the main test classes differ?

`SimpleTestCase` disallows database access by default. `TestCase` uses transaction-based isolation on supporting databases. `TransactionTestCase` allows testing real transaction behaviour and flushes data between tests. Use the database engine relevant to locking or constraints.

### 26. What does the test client prove?

It exercises Django's request-response behaviour without a real browser. Check permissions, redirects, forms and query budgets; use browser tests for JavaScript, layout and actual device behaviour. `assertNumQueries()` can guard against N+1 regressions.

### 27. What happens to the database in a test run?

Django normally creates a separate test database and removes it afterwards. `--keepdb` preserves it, and parallel runs can use clones. Explicitly verify test settings and database aliases; never assume a custom setup makes production access impossible.

## Deployment

### 28. Which settings need review before release?

Disable debug output, keep the secret key outside source control, set allowed hosts and configure HTTPS and secure cookies. Proxy trust must match the infrastructure. Run `check --deploy`, but do not mistake it for a complete security audit. Use the [deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).

### 29. How are static files served in production?

Collect assets into the configured static root and serve them through the production static-file setup. Development serving is not a deployment strategy. Keep uploaded media separate from application assets and treat uploads as untrusted.

### 30. How do WSGI and ASGI differ?

WSGI is the traditional synchronous application interface. ASGI supports asynchronous application patterns. The choice does not automatically make synchronous code non-blocking. Use a suitable production server; `runserver` is a development server.

## Practise beyond the short answers

Build a small project and deliberately investigate an N+1 query, a reversible data migration, a permission failure and a production configuration warning. Explain what failed, how you measured it and why the fix works. That is more persuasive than reciting terminology.

These public learning questions are not a published answer key to Rvion's assessment. Read the [Python/Django assessment briefing](/en/assessments/python-django-professional/about/) for its scope. For a project, explore [custom application development](/en/services/custom-web-application/) or [contact Rvion](/en/contact/).
