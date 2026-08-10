# Golang Echo Handler & Struct Parsing Reference

This guide details how to scan and parse Golang Echo framework files ending with `*_handler.go`.

---

## 1. Echo Route Registration Patterns

Identify route registrations in `*_handler.go` files or route registration functions:

### Router Grouping & Endpoints
- Direct Router: `e.POST("/api/v1/invoices", h.CreateInvoice)`
- Grouped Router:
  ```go
  g := e.Group("/api/v1/billing")
  g.POST("/invoices", h.CreateInvoice)
  g.PUT("/invoices/:id", h.UpdateInvoice)
  g.PATCH("/invoices/:id", h.PatchInvoice)
  g.DELETE("/invoices/:id", h.DeleteInvoice)
  ```

### Path Parameter Mapping
- Echo path parameter `:id` or `:invoice_id` must be mapped to `{id}` in the JSON audit configuration:
  - Go Echo Path: `/api/v1/invoices/:id`
  - Audit Config Path: `/api/v1/invoices/{id}`

---

## 2. Request Struct & JSON Tag Extraction

Locate handler functions and trace request binding:

```go
func (h *InvoiceHandler) CreateInvoice(c echo.Context) error {
    var req CreateInvoiceRequest
    if err := c.Bind(&req); err != nil {
        return c.JSON(http.StatusBadRequest, ...)
    }
    ...
}
```

Locate the corresponding Go struct:

```go
type CreateInvoiceRequest struct {
    InvoiceID string  `json:"invoice_id" validate:"required"`
    Amount    float64 `json:"amount" validate:"required,gt=0"`
    Status    string  `json:"status"`
}
```

### Struct Field Rules
1. Read the `json:"..."` struct tag to get the exact JSON property key name.
2. Ignore fields with `json:"-"`.
3. If struct tag is omitted, convert Go PascalCase field name to camelCase or snake_case.
4. Extract primary key field (`invoice_id`, `id`, `user_code`) for `id_field`.

---

## 3. Inferring Valid Sample Values

| Go Data Type | Sample Value Rules |
| :--- | :--- |
| `string` | Realistic string formatted for field name (e.g. `invoice_id` -> `"INV-2026-001"`). |
| `int`, `int64` | Positive integer (e.g. `100`). |
| `float64` | Decimal number (e.g. `150.50`). |
| `bool` | `true` or `false`. |
| `time.Time` | ISO 8601 string (e.g. `"2026-08-10T12:00:00Z"`). |
| `[]string` | `["item_1", "item_2"]`. |
