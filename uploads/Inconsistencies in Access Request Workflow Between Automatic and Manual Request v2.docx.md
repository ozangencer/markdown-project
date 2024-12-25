
# Inconsistencies in Access Request Workflow Between Automatic and Manual Requests

1. We have a business rule set that we created based on events coming from SuccessFactors (such as HIRNEW, TRANHIRE, RESIGNATION, etc.). Therefore, when we run an HR Trigger job, a request can be automatically generated based on these events and sent to the approval workflow.
2. This problem is available in the SuccessFactors Test and Dev systems yet. However, the SF Prod system is not connected to our IAG Non-Prod. You can access the connected SF systems using the credentials below:

**SF Test:** Company: yasarholdiT1

Username: admin\_iag

Password: Sap.2025

**SF Dev:** Company: yasarholdiD

Username: admin\_iag

Password: Sap.2025

1. Affected user is Melih Pirlepeli (214) . The user exists in SF Test system.
2. First, we select an event from the Reprocess Missed HR Events report that could not be processed due to a defined business rule, to reprocess it. For example, the user Sancar Yıldırım, the user exists in SF Test System:![A screenshot of a computer

   Description automatically generated](data:image/png;base64...)

The user's manager is defined in IAS and reflected in IAG through the Repo Job. Similarly, the manager has roles such as IAG\_WF\_MANAGER.![A screenshot of a website

Description automatically generated](data:image/png;base64...)

After selecting the user Sancar Yıldırım and retrying, we run an HR Trigger job again and see in the logs that the request is automatically created: ![A screenshot of a job history list

Description automatically generated](data:image/png;base64...)

![A screenshot of a computer

Description automatically generated](data:image/png;base64...)

Similarly, in the Request Administration screen, instead of being sent only to the manager as the approver, the request is sent to the entire security group excluding the manager.![](data:image/png;base64...)

However, when we manually create a role request for Sancar Yıldırım using the Create Access Request for Others application, the manager is automatically assigned, and when the request is submitted, it is sent only to the manager for approval.![A screenshot of a login page

Description automatically generated](data:image/png;base64...)

![A screenshot of a phone

Description automatically generated](data:image/png;base64...)

![A screenshot of a computer

Description automatically generated](data:image/png;base64...)

