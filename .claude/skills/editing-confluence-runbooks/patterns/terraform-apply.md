# Pattern: Terraform Apply

**Use when** a runbook step changes infrastructure through Terraform.

> Status: SKELETON — the owner will supply the real procedure and parameter list. Fill every `{{SLOT}}`; anything you can't fill → stop and ask.

## Fixed sequence

| STG | PRD |
|---|---|
| 1. Run **plan** job (whitelist `tf-plan`) with parameter table | 1. Confirm change ticket `{{CHANGE_TICKET}}` is approved and you are inside the window |
| 2. Review plan: counts match expectation; unexpected `destroy` → stop | 2. Run **plan** job with PRD parameter table |
| 3. Run **apply** job (whitelist `tf-apply`) referencing the plan build | 3. Second reviewer checks plan output; unexpected `destroy` → stop |
| Verify | 4. Run **apply** job referencing the reviewed plan build |
| | 5. Announce completion in `{{ANNOUNCE_CHANNEL}}` |
| | Verify |

## Slots

| Slot | Meaning |
|---|---|
| `{{STEP_NO}}`, `{{STEP_TITLE}}` | Step number and title |
| `{{TF_PLAN_URL}}`, `{{TF_APPLY_URL}}` | Whitelist keys `tf-plan`, `tf-apply` |
| `{{TF_WORKSPACE_STG}}`, `{{TF_WORKSPACE_PRD}}` | Terraform workspace per env |
| Parameter rows | Parameter list (owner to provide) |
| `{{EXPECTED_PLAN}}` | e.g. `0 to add, 1 to change, 0 to destroy` |
| `{{CHANGE_TICKET}}`, `{{ANNOUNCE_CHANNEL}}` | PRD only |

## Storage-format template

```xml
<h2>Step {{STEP_NO}}: {{STEP_TITLE}}</h2>
<p>Apply Terraform change via Jenkins: plan → review → apply.</p>

<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">STG – 3 steps</ac:parameter>
  <ac:rich-text-body>
    <ol>
      <li><p>Open <a href="{{TF_PLAN_URL}}">Terraform plan job</a> → <em>Build with Parameters</em>:</p>
        <table><tbody>
          <tr><th>Parameter</th><th>Value</th><th>Notes</th></tr>
          <tr><td>ENVIRONMENT</td><td>stg</td><td></td></tr>
          <tr><td>TF_WORKSPACE</td><td>{{TF_WORKSPACE_STG}}</td><td></td></tr>
          <tr><td>{{PARAM}}</td><td>{{STG_VALUE}}</td><td>{{NOTE}}</td></tr>
        </tbody></table></li>
      <li><p>Review plan output. Expected: <code>{{EXPECTED_PLAN}}</code>. Any unexpected <code>destroy</code> → stop.</p></li>
      <li><p>Open <a href="{{TF_APPLY_URL}}">Terraform apply job</a> with the same parameters + <code>PLAN_BUILD_NUMBER</code> from step 1.</p></li>
    </ol>
    <h4>Verify</h4>
    <table><tbody>
      <tr><th>Check</th><th>Expected</th><th>If it fails</th></tr>
      <tr><td>Apply job console</td><td><code>Apply complete!</code> with counts equal to the plan</td><td>Stop; re-run plan to inspect drift</td></tr>
      <tr><td>Re-run plan job</td><td><code>No changes.</code></td><td>Investigate drift before PRD</td></tr>
    </tbody></table>
  </ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">PRD – 5 steps</ac:parameter>
  <ac:rich-text-body>
    <ol>
      <li><p>Confirm change ticket <strong>{{CHANGE_TICKET}}</strong> is approved and current time is inside the window.</p></li>
      <li><p>Open <a href="{{TF_PLAN_URL}}">Terraform plan job</a> → <em>Build with Parameters</em>:</p>
        <table><tbody>
          <tr><th>Parameter</th><th>Value</th><th>Notes</th></tr>
          <tr><td>ENVIRONMENT</td><td>prd</td><td></td></tr>
          <tr><td>TF_WORKSPACE</td><td>{{TF_WORKSPACE_PRD}}</td><td></td></tr>
          <tr><td>{{PARAM}}</td><td>{{PRD_VALUE}}</td><td>{{NOTE}}</td></tr>
        </tbody></table></li>
      <li><p>Second reviewer checks the plan output. Expected: <code>{{EXPECTED_PLAN}}</code>. Any unexpected <code>destroy</code> → stop.</p></li>
      <li><p>Open <a href="{{TF_APPLY_URL}}">Terraform apply job</a> with the same parameters + reviewed <code>PLAN_BUILD_NUMBER</code>.</p></li>
      <li><p>Announce completion in <strong>{{ANNOUNCE_CHANNEL}}</strong>.</p></li>
    </ol>
    <h4>Verify</h4>
    <table><tbody>
      <tr><th>Check</th><th>Expected</th><th>If it fails</th></tr>
      <tr><td>Apply job console</td><td><code>Apply complete!</code> with counts equal to the reviewed plan</td><td>Stop; escalate to infra on-call</td></tr>
      <tr><td>Re-run plan job</td><td><code>No changes.</code></td><td>Escalate</td></tr>
    </tbody></table>
  </ac:rich-text-body>
</ac:structured-macro>
```
