--jinja
-- =============================================================================
-- Snowflake Workload Identity Federation (WIDF) Setup for AWS App Runner
-- Reference: https://docs.snowflake.com/en/user-guide/workload-identity-federation#configure-aws
-- =============================================================================
-- Prerequisites:
--   1. AWS Account ID
--   2. App Runner Instance Role created and attached to App Runner service
--   3. Snowflake role with appropriate permissions (from setup.sql)
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- =============================================================================
-- Variables (Replace with your values)
-- =============================================================================
-- Example values:
--   AWS Account ID:      123456789012
--   Instance Role Name:  apprunner-snowflake-demo-instance-role
--   Snowflake User:      APPRUNNER_DEMO_USER
--   Snowflake Role:      DEMO_DB_SA (from setup.sql)
-- =============================================================================

SET aws_account_id = '<%aws_account_id%>';
SET instance_role_name = '<%instance_role_name%>';
SET snowflake_user = '<%snowflake_user%>';
SET snowflake_role = '<%sa_role%>';

-- =============================================================================
-- Step 1: Create Snowflake Service User with Workload Identity
-- =============================================================================
-- This creates a SERVICE user that authenticates via AWS IAM role
-- No security integrations needed for AWS IAM - Snowflake validates directly

CREATE USER IF NOT EXISTS IDENTIFIER($snowflake_user)
    WORKLOAD_IDENTITY = (
        TYPE = AWS_IAM
        AWS_ROLE_ARN = CONCAT('arn:aws:iam::', $aws_account_id, ':role/', $instance_role_name)
    )
    TYPE = SERVICE
    DEFAULT_ROLE = IDENTIFIER($snowflake_role)
    DEFAULT_WAREHOUSE = 'COMPUTE_WH'
    COMMENT = 'Service user for AWS App Runner workload identity federation';

-- =============================================================================
-- Step 2: Grant Role to Service User
-- =============================================================================

GRANT ROLE IDENTIFIER($snowflake_role) TO USER IDENTIFIER($snowflake_user);

-- =============================================================================
-- Verification Queries
-- =============================================================================

-- View user configuration
DESCRIBE USER IDENTIFIER($snowflake_user);

-- View workload identity authentication methods for the user
SHOW USER WORKLOAD IDENTITY AUTHENTICATION METHODS FOR USER IDENTIFIER($snowflake_user);

-- =============================================================================
-- AWS App Runner Configuration
-- =============================================================================
-- 1. Create Instance Role with trust policy for tasks.apprunner.amazonaws.com
--    (see config/apprunner-instance-trust-policy.json)
--
-- 2. Attach the Instance Role to your App Runner service
--
-- 3. Set these environment variables in App Runner:
--    DEPLOYMENT_ENV=AWS
--    SNOWFLAKE_ACCOUNT=<your-account-identifier>
--    SNOWFLAKE_USER=<value of snowflake_user above>
--    SNOWFLAKE_ROLE=<value of snowflake_role above>
--    SNOWFLAKE_WAREHOUSE=COMPUTE_WH
--    DEMO_DATABASE=DEMO_DB
-- =============================================================================
